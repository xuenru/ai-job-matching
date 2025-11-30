"""Match Agent for scoring and ranking job matches using ADK."""

from core.logger import get_logger
from core.parsing_schemas import (
    JobSchema,
    RankedJob,
    RankedJobsOutput,
    ResumeSchema,
    ScoreBreakdown,
)
from core.scoring import JobMatcher
from core.utils import write_json_file


class MatchAgent:
    """Agent responsible for matching resume with jobs and generating rankings."""

    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.matcher = JobMatcher()
        self.logger = get_logger()

        # Initialize ADK client (optional - for real LLM calls)
        # For prototype, we use deterministic reasoning
        self.use_llm = False

    def match_jobs(
        self,
        resume: ResumeSchema,
        jobs: list[JobSchema],
        output_path: str = "output/ranked_jobs.json",
    ) -> RankedJobsOutput:
        """
        Match resume with all jobs and produce ranked results.
        """
        self.logger.info(f"Matching resume with {len(jobs)} jobs")

        ranked_jobs = []

        for job in jobs:
            try:
                # Calculate match score
                score, breakdown, matched_skills, missing_skills = (
                    self.matcher.calculate_match_score(resume, job)
                )

                # Determine success likelihood
                success_likelihood = self.matcher.determine_success_likelihood(score)

                # Generate explanation and evidence
                reason, evidence_snippets = self._generate_explanation(
                    resume, job, score, breakdown, matched_skills, missing_skills
                )

                # Create ranked job entry
                ranked_job = RankedJob(
                    id=job.id,
                    score=score,
                    score_breakdown=breakdown,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    reason=reason,
                    matched_skills=matched_skills[:10],  # Limit to top 10
                    missing_skills=missing_skills[:5],  # Limit to top 5
                    evidence_snippets=evidence_snippets,
                    success_likelihood=success_likelihood,
                )

                ranked_jobs.append(ranked_job)

                self.logger.increment_metric("matches_computed")

            except Exception as e:
                self.logger.error(f"Error matching job {job.id}: {e}")

        # Sort by score (descending)
        ranked_jobs.sort(key=lambda x: x.score, reverse=True)

        # Create output
        output = RankedJobsOutput(ranked_jobs=ranked_jobs)

        # Save to file
        write_json_file(output_path, output.model_dump())
        self.logger.info(f"Ranked jobs saved to {output_path}")

        return output

    def _generate_explanation(
        self,
        resume: ResumeSchema,
        job: JobSchema,
        score: float,
        breakdown: ScoreBreakdown,
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> tuple[str, list[str]]:
        """
        Generate human-readable explanation for the match.
        Returns: (reason, evidence_snippets)
        """
        if self.use_llm:
            return self._generate_with_llm(
                resume, job, score, breakdown, matched_skills, missing_skills
            )
        else:
            return self._generate_deterministic(
                resume, job, score, breakdown, matched_skills, missing_skills
            )

    def _generate_deterministic(
        self,
        resume: ResumeSchema,
        job: JobSchema,
        score: float,
        breakdown: ScoreBreakdown,
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> tuple[str, list[str]]:
        """
        Generate explanation using rule-based logic.
        """
        # Build reason text
        reason_parts = []

        # Overall fit
        if score >= 75:
            reason_parts.append("Excellent match with strong alignment across all criteria.")
        elif score >= 55:
            reason_parts.append("Good match with solid alignment in key areas.")
        else:
            reason_parts.append("Moderate match with some gaps to consider.")

        # Skill match
        if breakdown.skill_match >= 30:
            reason_parts.append(f"Strong skill alignment ({len(matched_skills)} matched skills).")
        elif breakdown.skill_match >= 20:
            reason_parts.append(f"Good skill coverage ({len(matched_skills)} matched skills).")
        else:
            reason_parts.append(
                f"Limited skill overlap (only {len(matched_skills)} matched skills)."
            )

        # Experience alignment
        if breakdown.experience_alignment >= 20:
            reason_parts.append("Extensive relevant experience in the domain.")
        elif breakdown.experience_alignment >= 15:
            reason_parts.append("Solid experience relevant to the role.")
        else:
            reason_parts.append("Some relevant experience but not perfectly aligned.")

        # Seniority fit
        if breakdown.seniority_fit >= 8:
            reason_parts.append("Seniority level matches role requirements.")
        elif breakdown.seniority_fit >= 5:
            reason_parts.append("Seniority level reasonably aligned.")
        else:
            reason_parts.append("Seniority level may not be ideal fit.")

        # Location/language
        if breakdown.location_language >= 8:
            reason_parts.append("Location and language requirements well met.")
        elif breakdown.location_language >= 5:
            reason_parts.append("Location and language mostly aligned.")

        # Missing skills warning
        if len(missing_skills) > 0:
            reason_parts.append(f"Note: Missing {len(missing_skills)} key requirements.")

        reason = " ".join(reason_parts)

        # Extract evidence snippets from job description
        evidence_snippets = []

        # Add responsibility snippets that match candidate's experience
        if job.responsibilities:
            resp_sentences = job.responsibilities.split(".")
            for sentence in resp_sentences[:3]:  # Take first 3 sentences
                sentence = sentence.strip()
                if len(sentence) > 20:
                    evidence_snippets.append(sentence + ".")

        # Add requirement snippets
        for req in job.requirements[:3]:  # Take first 3 requirements
            evidence_snippets.append(req)

        return reason, evidence_snippets[:5]  # Limit to 5 snippets

    def _generate_with_llm(
        self,
        resume: ResumeSchema,
        job: JobSchema,
        score: float,
        breakdown: ScoreBreakdown,
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> tuple[str, list[str]]:
        """
        Generate explanation using LLM (for future implementation).
        """
        self.logger.increment_metric("llm_calls")

        # This would use ADK's LLM capabilities to generate natural language explanation
        # For now, fall back to deterministic
        return self._generate_deterministic(
            resume, job, score, breakdown, matched_skills, missing_skills
        )
