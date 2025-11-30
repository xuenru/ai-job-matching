"""Scoring logic for job-resume matching."""

from core.embeddings import get_embeddings
from core.logger import get_logger
from core.parsing_schemas import JobSchema, ResumeSchema, ScoreBreakdown


class JobMatcher:
    """Job matching and scoring engine."""

    def __init__(self):
        self.embeddings = get_embeddings()
        self.logger = get_logger()

    def calculate_skill_match(
        self, resume: ResumeSchema, job: JobSchema
    ) -> tuple[float, list[str], list[str]]:
        """
        Calculate skill match score (0-40 points).
        Returns: (score, matched_skills, missing_skills)
        """
        resume_skills = {s.lower() for s in resume.skills}
        job_requirements = {r.lower() for r in job.requirements}
        job_nice_to_have = {n.lower() for n in job.nice_to_have}

        # Find matches
        matched_required = resume_skills & job_requirements
        matched_nice = resume_skills & job_nice_to_have

        # Find missing
        missing_required = job_requirements - resume_skills

        # Calculate score
        total_requirements = len(job_requirements)
        if total_requirements == 0:
            # If no specific requirements, use general skill overlap
            all_job_skills = job_requirements | job_nice_to_have
            if len(all_job_skills) == 0:
                return 30.0, [], []
            match_ratio = len(resume_skills & all_job_skills) / len(all_job_skills)
            score = match_ratio * 35
        else:
            required_ratio = len(matched_required) / total_requirements
            score = required_ratio * 35  # Up to 35 points for required

        # Add bonus for nice-to-have (up to 5 points)
        if len(job_nice_to_have) > 0:
            nice_ratio = len(matched_nice) / len(job_nice_to_have)
            score += nice_ratio * 5

        # Cap at 40
        score = min(score, 40.0)

        matched_skills = list(matched_required | matched_nice)
        missing_skills = list(missing_required)

        return score, matched_skills, missing_skills

    def calculate_experience_alignment(self, resume: ResumeSchema, job: JobSchema) -> float:
        """
        Calculate experience/domain alignment score (0-30 points).
        """
        score = 0.0

        # Domain alignment (up to 15 points)
        resume_domains = {d.lower() for d in resume.domains}
        job_text_lower = (
            job.title + " " + job.responsibilities + " ".join(job.requirements)
        ).lower()

        domain_matches = 0
        for domain in resume_domains:
            if domain in job_text_lower:
                domain_matches += 1

        if len(resume_domains) > 0:
            domain_score = (domain_matches / len(resume_domains)) * 15
            score += domain_score

        # Years of experience alignment (up to 15 points)
        # Extract years from job requirements
        required_years = self._extract_years_from_text(" ".join(job.requirements))

        if required_years > 0:
            years_diff = abs(resume.years_of_experience - required_years)
            if years_diff == 0:
                score += 15
            elif years_diff <= 2:
                score += 12
            elif years_diff <= 5:
                score += 8
            else:
                score += 5
        else:
            # No specific years requirement, give moderate score
            score += 10

        return min(score, 30.0)

    def calculate_seniority_fit(self, resume: ResumeSchema, job: JobSchema) -> float:
        """
        Calculate seniority fit score (0-10 points).
        """
        seniority_levels = {
            "junior": 1,
            "mid": 2,
            "intermediate": 2,
            "senior": 3,
            "lead": 4,
            "staff": 4,
            "principal": 5,
            "architect": 5,
        }

        resume_level = seniority_levels.get(resume.seniority.lower(), 2)

        # Extract seniority from job
        job_seniority = job.seniority.lower() if job.seniority else ""
        job_text = (job.title + " " + " ".join(job.requirements)).lower()

        job_level = 2  # Default to mid
        for key, level in seniority_levels.items():
            if key in job_seniority or key in job_text:
                job_level = level
                break

        # Calculate fit
        level_diff = abs(resume_level - job_level)
        if level_diff == 0:
            return 10.0
        elif level_diff == 1:
            return 7.0
        elif level_diff == 2:
            return 4.0
        else:
            return 2.0

    def calculate_location_language_fit(self, resume: ResumeSchema, job: JobSchema) -> float:
        """
        Calculate location and language fit score (0-10 points).
        """
        score = 0.0

        # Location fit (up to 5 points)
        job_location_lower = job.location.lower()
        preferred_location_lower = resume.contact.location.lower()

        if (
            preferred_location_lower in job_location_lower
            or job_location_lower in preferred_location_lower
        ):
            score += 5
        elif any(word in job_location_lower for word in ["remote", "anywhere"]):
            score += 4
        else:
            score += 2

        # Language fit (up to 5 points)
        resume_languages = {lang.lower() for lang in resume.languages}
        job_text = (job.title + " " + job.responsibilities + " ".join(job.requirements)).lower()

        # Check for language requirements
        if "french" in job_text or "français" in job_text:
            if "french" in resume_languages or "français" in resume_languages:
                score += 5
            else:
                score += 1
        elif "english" in job_text:
            if "english" in resume_languages:
                score += 5
            else:
                score += 2
        else:
            # No specific language requirement
            score += 4

        return min(score, 10.0)

    def calculate_semantic_similarity(self, resume: ResumeSchema, job: JobSchema) -> float:
        """
        Calculate semantic similarity score (0-10 points).
        Uses embeddings to compare overall profile with job description.
        """
        # Create resume summary
        resume_text = (
            f"{' '.join(resume.skills)} {' '.join(resume.domains)} {' '.join(resume.projects)}"
        )

        # Create job summary
        job_text = f"{job.title} {job.responsibilities} {' '.join(job.requirements)}"

        # Calculate similarity
        similarity = self.embeddings.cosine_similarity(resume_text, job_text)

        # Scale to 0-10
        score = similarity * 10

        return max(0.0, min(score, 10.0))

    def calculate_match_score(
        self, resume: ResumeSchema, job: JobSchema
    ) -> tuple[float, ScoreBreakdown, list[str], list[str]]:
        """
        Calculate overall match score and breakdown.
        Returns: (total_score, breakdown, matched_skills, missing_skills)
        """
        # Calculate individual scores
        skill_score, matched_skills, missing_skills = self.calculate_skill_match(resume, job)
        experience_score = self.calculate_experience_alignment(resume, job)
        seniority_score = self.calculate_seniority_fit(resume, job)
        location_score = self.calculate_location_language_fit(resume, job)
        semantic_score = self.calculate_semantic_similarity(resume, job)

        # Create breakdown
        breakdown = ScoreBreakdown(
            skill_match=round(skill_score, 2),
            experience_alignment=round(experience_score, 2),
            seniority_fit=round(seniority_score, 2),
            location_language=round(location_score, 2),
            semantic_alignment=round(semantic_score, 2),
        )

        # Calculate total
        total_score = (
            skill_score + experience_score + seniority_score + location_score + semantic_score
        )

        self.logger.debug(f"Job {job.id} - Total Score: {total_score:.2f}")

        return round(total_score, 2), breakdown, matched_skills, missing_skills

    def determine_success_likelihood(self, score: float) -> str:
        """Determine success likelihood based on score."""
        if score >= 75:
            return "High"
        elif score >= 55:
            return "Medium"
        else:
            return "Low"

    def _extract_years_from_text(self, text: str) -> int:
        """Extract years of experience from text."""
        import re

        text = text.lower()

        # Look for patterns like "3+ years", "5 years", "3-5 years"
        patterns = [
            r"(\d+)\+?\s*years?",
            r"(\d+)\s*-\s*\d+\s*years?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        return 0
