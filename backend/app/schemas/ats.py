"""
ATS (Applicant Tracking System) scoring schemas.

Defines models for job description analysis, keyword matching,
and ATS compatibility scoring.
"""

from typing import Any

from pydantic import BaseModel, Field


class JobDescriptionData(BaseModel):
    """Extracted data from a job description."""

    job_title: str | None = Field(None, description="Job title/position")
    company_name: str | None = Field(None, description="Hiring company name")
    location: str | None = Field(None, description="Job location")
    job_type: str | None = Field(
        None, description="Full-time, Part-time, Contract, etc."
    )
    experience_required: str | None = Field(
        None, description="Required years of experience"
    )
    experience_years_min: int | None = Field(
        None, description="Minimum years of experience"
    )
    experience_years_max: int | None = Field(
        None, description="Maximum years of experience"
    )

    # Skills extracted from JD
    required_skills: list[str] = Field(
        default_factory=list, description="Must-have skills"
    )
    preferred_skills: list[str] = Field(
        default_factory=list, description="Nice-to-have skills"
    )

    # Education requirements
    required_education: str | None = Field(None, description="Required education level")
    preferred_education: str | None = Field(
        None, description="Preferred education level"
    )

    # Certifications
    required_certifications: list[str] = Field(default_factory=list)
    preferred_certifications: list[str] = Field(default_factory=list)

    # Keywords for ATS matching
    keywords: list[str] = Field(
        default_factory=list, description="All extracted keywords"
    )

    # Responsibilities
    responsibilities: list[str] = Field(default_factory=list)

    # Benefits mentioned
    benefits: list[str] = Field(default_factory=list)

    # Salary if mentioned
    salary_range: str | None = Field(None)


class SkillMatch(BaseModel):
    """A single skill match result."""

    skill: str = Field(..., description="The skill name")
    found_in_resume: bool = Field(..., description="Whether skill was found")
    match_type: str = Field("exact", description="exact, partial, or synonym")
    resume_evidence: str | None = Field(
        None, description="Where in resume it was found"
    )


class ATSScoreResult(BaseModel):
    """ATS compatibility score result."""

    ats_score: int = Field(..., ge=0, le=100, description="ATS score 0-100")

    # Breakdown
    keyword_match_score: int = Field(..., ge=0, le=100)
    skills_match_score: int = Field(..., ge=0, le=100)
    experience_match_score: int = Field(..., ge=0, le=100)
    education_match_score: int = Field(..., ge=0, le=100)

    # Matched and missing
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    missing_preferred_skills: list[str] = Field(default_factory=list)

    # Skill match details
    skill_matches: list[SkillMatch] = Field(default_factory=list)

    # Suggestions for improvement
    suggestions: list[str] = Field(default_factory=list)

    # Summary
    summary: str = Field("", description="Brief ATS score explanation")


class ResumeJDAnalysisRequest(BaseModel):
    """Request for resume-JD analysis (when using text input)."""

    job_description_text: str | None = Field(
        None, description="Job description as text"
    )


class ResumeJDAnalysisResult(BaseModel):
    """Complete result of resume vs job description analysis."""

    success: bool = Field(True)

    # Candidate info (from resume)
    candidate_name: str | None = None
    candidate_email: str | None = None
    candidate_current_role: str | None = None
    candidate_experience_years: float | None = None

    # Job info (from JD)
    job_title: str | None = None
    company_name: str | None = None

    # ATS Score
    ats_result: ATSScoreResult | None = None

    # Full extracted data
    resume_data: dict[str, Any] = Field(default_factory=dict)
    jd_data: dict[str, Any] = Field(default_factory=dict)

    # Processing info
    processing_time_ms: float = 0

    # Error if failed
    error: str | None = None
