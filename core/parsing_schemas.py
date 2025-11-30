"""Data schemas for resume and job parsing."""

from pydantic import BaseModel, Field


class Contact(BaseModel):
    """Contact information schema."""

    email: str = ""
    location: str = ""
    phone: str | None = None


class ResumeSchema(BaseModel):
    """Structured resume schema."""

    name: str
    contact: Contact
    years_of_experience: int
    seniority: str  # Junior, Mid, Senior, Lead, etc.
    skills: list[str]
    domains: list[str]
    languages: list[str]
    education: list[str]
    projects: list[str]
    preferred_location: str = "France"
    other_notes: str = ""


class JobSchema(BaseModel):
    """Structured job posting schema."""

    id: str
    title: str
    company: str
    location: str
    contract: str = "Full-time"
    responsibilities: str
    requirements: list[str]
    nice_to_have: list[str]
    seniority: str = ""
    raw_text: str


class ScoreBreakdown(BaseModel):
    """Score breakdown for match evaluation."""

    skill_match: float = Field(ge=0, le=40)
    experience_alignment: float = Field(ge=0, le=30)
    seniority_fit: float = Field(ge=0, le=10)
    location_language: float = Field(ge=0, le=10)
    semantic_alignment: float = Field(ge=0, le=10)


class RankedJob(BaseModel):
    """Ranked job result with match details."""

    id: str
    score: float
    score_breakdown: ScoreBreakdown
    title: str
    company: str
    location: str
    reason: str
    matched_skills: list[str]
    missing_skills: list[str]
    evidence_snippets: list[str]
    success_likelihood: str  # High, Medium, Low


class RankedJobsOutput(BaseModel):
    """Final output schema for ranked jobs."""

    ranked_jobs: list[RankedJob]
