"""
ATS (Applicant Tracking System) services.

Provides keyword matching, skill comparison, and ATS scoring.
"""

from app.services.ats.scorer import (
    ATSAnalyzer,
    get_ats_analyzer,
    get_skill_variations,
    normalize_skill,
    skills_match,
)

__all__ = [
    "ATSAnalyzer",
    "get_ats_analyzer",
    "skills_match",
    "normalize_skill",
    "get_skill_variations",
]
