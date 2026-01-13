"""
Candidate fit scoring and red flag detection schemas.

Defines models for candidate analysis, red flags, and recommendations.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RedFlagSeverity(str, Enum):
    """Severity level of a red flag."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RedFlagType(str, Enum):
    """Types of red flags that can be detected."""

    SHORT_TENURE = "short_tenure"
    EMPLOYMENT_GAP = "employment_gap"
    OVERQUALIFIED = "overqualified"
    UNDERQUALIFIED = "underqualified"
    FREQUENT_JOB_CHANGES = "frequent_job_changes"
    CAREER_REGRESSION = "career_regression"
    OVERLAPPING_JOBS = "overlapping_jobs"
    MISSING_RECENT_EXPERIENCE = "missing_recent_experience"
    NO_PROGRESSION = "no_progression"
    EDUCATION_MISMATCH = "education_mismatch"
    SKILL_GAPS = "skill_gaps"
    OTHER = "other"


class RecommendationType(str, Enum):
    """Recommendation categories."""

    STRONG_HIRE = "strong_hire"
    GOOD_FIT = "good_fit"
    POTENTIAL_FIT = "potential_fit"
    NEEDS_REVIEW = "needs_review"
    NOT_RECOMMENDED = "not_recommended"


class RedFlag(BaseModel):
    """A detected red flag in a candidate's resume."""

    flag_type: RedFlagType = Field(..., description="Type of red flag")
    severity: RedFlagSeverity = Field(..., description="Severity level")
    title: str = Field(..., description="Short title for the flag")
    description: str = Field(..., description="Detailed explanation")
    evidence: str | None = Field(None, description="Specific evidence from resume")
    suggestion: str | None = Field(None, description="How to address in interview")


class StrengthItem(BaseModel):
    """A strength identified in the candidate."""

    category: str = Field(
        ..., description="Category (skills, experience, education, etc.)"
    )
    title: str = Field(..., description="Short strength title")
    description: str = Field(..., description="Detailed explanation")
    relevance_score: int = Field(
        80, ge=0, le=100, description="How relevant to the role"
    )


class CareerProgression(BaseModel):
    """Analysis of career progression."""

    trajectory: str = Field(..., description="upward, lateral, downward, or mixed")
    avg_tenure_months: float = Field(..., description="Average job tenure in months")
    longest_tenure_months: int = Field(..., description="Longest tenure at one company")
    total_companies: int = Field(..., description="Number of unique companies")
    has_leadership_progression: bool = Field(False)
    progression_summary: str = Field("", description="Brief summary of career path")


class FitScoreBreakdown(BaseModel):
    """Breakdown of the fit score components."""

    skills_alignment: int = Field(..., ge=0, le=100)
    experience_match: int = Field(..., ge=0, le=100)
    education_fit: int = Field(..., ge=0, le=100)
    career_trajectory: int = Field(..., ge=0, le=100)
    cultural_signals: int = Field(..., ge=0, le=100)


class CandidateFitResult(BaseModel):
    """Complete candidate fit analysis result."""

    # Core scores
    fit_score: int = Field(..., ge=0, le=100, description="Overall fit score")
    fit_score_breakdown: FitScoreBreakdown | None = None

    # Recommendation
    recommendation: RecommendationType = Field(...)
    recommendation_text: str = Field(..., description="Human-readable recommendation")

    # Strengths and weaknesses
    strengths: list[StrengthItem] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)

    # Red flags
    red_flags: list[RedFlag] = Field(default_factory=list)
    red_flag_count: int = Field(0)
    has_critical_red_flags: bool = Field(False)

    # Career analysis
    career_progression: CareerProgression | None = None

    # Executive summary
    executive_summary: str = Field(
        "", description="One-paragraph summary for recruiters"
    )

    # Interview suggestions
    interview_questions: list[str] = Field(default_factory=list)

    # Salary/level fit
    suggested_level: str | None = Field(
        None, description="Junior, Mid, Senior, Lead, etc."
    )

    # Processing metadata
    analysis_confidence: float = Field(0.8, ge=0, le=1)


class FullCandidateAnalysis(BaseModel):
    """Complete analysis combining ATS score and fit analysis."""

    success: bool = Field(True)

    # Candidate info
    candidate_name: str | None = None
    candidate_email: str | None = None
    candidate_current_role: str | None = None
    candidate_experience_years: float | None = None

    # Job info
    job_title: str | None = None
    company_name: str | None = None

    # Combined score (weighted: 40% ATS + 60% Fit)
    overall_score: int = Field(0, ge=0, le=100)

    # ATS results (from Phase 2)
    ats_score: int = Field(0, ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)

    # Fit analysis
    fit_analysis: CandidateFitResult | None = None

    # Full data
    resume_data: dict[str, Any] = Field(default_factory=dict)
    jd_data: dict[str, Any] = Field(default_factory=dict)

    # Processing
    processing_time_ms: float = 0
    error: str | None = None


class CandidateRankingScore(BaseModel):
    """Individual candidate ranking score."""

    rank: int = Field(..., description="Ranking position (1 = best)")
    file_name: str = Field(..., description="Name of the resume file")
    candidate_name: str | None = Field(None)
    overall_score: int = Field(..., ge=0, le=100)
    ats_score: int = Field(..., ge=0, le=100)
    fit_score: int = Field(..., ge=0, le=100)
    recommendation: RecommendationType = Field(...)
    strengths_count: int = Field(default=0)
    red_flags_count: int = Field(default=0)
    has_critical_red_flags: bool = Field(False)
    suggested_level: str | None = Field(None)
    executive_summary: str | None = Field(None)


class CandidateComparison(BaseModel):
    """Comparison between two or more candidates."""

    file_name_1: str
    file_name_2: str

    # Scores
    overall_score_1: int
    overall_score_2: int
    overall_score_diff: int  # Positive if candidate 1 is higher

    # ATS comparison
    ats_score_1: int
    ats_score_2: int

    # Fit comparison
    fit_score_1: int
    fit_score_2: int

    # Skills matching
    matched_skills_1: list[str]
    matched_skills_2: list[str]
    unique_skills_1: list[str]  # Skills only in candidate 1
    unique_skills_2: list[str]  # Skills only in candidate 2
    common_skills: list[str]

    # Red flags
    red_flags_1: int
    red_flags_2: int
    critical_flags_1: bool
    critical_flags_2: bool

    # Recommendations
    recommendation_1: RecommendationType
    recommendation_2: RecommendationType

    # Winner (which is better for the role)
    winner: int = Field(1, description="1 or 2")
    winner_reason: str = Field(description="Why one candidate is better")


class RankingResult(BaseModel):
    """Result of multi-resume ranking."""

    success: bool = Field(True)

    # Job info
    job_title: str | None = None
    company_name: str | None = None

    # Rankings
    total_candidates: int = Field(..., description="Total number of candidates ranked")
    rankings: list[CandidateRankingScore] = Field(
        ..., description="Candidates ranked by score"
    )

    # Top candidate
    top_candidate: CandidateRankingScore | None = None
    top_candidate_analysis: FullCandidateAnalysis | None = None

    # Full analyses
    all_analyses: dict[str, FullCandidateAnalysis] = Field(
        default_factory=dict,
        description="Full analysis for each candidate (keyed by file name)",
    )

    # Comparison insights
    score_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of scores (e.g. 'high': 2, 'medium': 3, 'low': 1)",
    )
    average_score: float = Field(0)

    # Recommendations
    hiring_recommendation: str = Field(description="Overall hiring recommendation")

    # Processing
    processing_time_ms: float = 0
    error: str | None = None
