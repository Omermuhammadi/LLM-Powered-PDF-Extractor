"""
ATS (Applicant Tracking System) scoring service.

Provides keyword matching, skill comparison, and ATS scoring
between resumes and job descriptions.
"""

import re
from dataclasses import dataclass
from typing import Any

from app.core import logger
from app.schemas.ats import ATSScoreResult, SkillMatch

# Common skill synonyms/variations for fuzzy matching
SKILL_SYNONYMS: dict[str, list[str]] = {
    "javascript": ["js", "ecmascript", "es6", "es2015"],
    "typescript": ["ts"],
    "python": ["py", "python3", "python2"],
    "kubernetes": ["k8s", "kube"],
    "postgresql": ["postgres", "psql", "pgsql"],
    "mongodb": ["mongo"],
    "elasticsearch": ["elastic", "es"],
    "amazon web services": ["aws"],
    "google cloud platform": ["gcp", "google cloud"],
    "microsoft azure": ["azure"],
    "machine learning": ["ml"],
    "artificial intelligence": ["ai"],
    "natural language processing": ["nlp"],
    "continuous integration": ["ci"],
    "continuous deployment": ["cd"],
    "ci/cd": ["cicd", "ci-cd", "continuous integration/continuous deployment"],
    "react": ["reactjs", "react.js"],
    "node": ["nodejs", "node.js"],
    "vue": ["vuejs", "vue.js"],
    "angular": ["angularjs", "angular.js"],
    "dotnet": [".net", "dot net", "asp.net"],
    "csharp": ["c#", "c sharp"],
    "cpp": ["c++", "cplusplus"],
    "sql server": ["mssql", "microsoft sql server"],
    "restful": ["rest", "rest api", "restful api"],
    "graphql": ["gql"],
    "docker": ["containerization", "containers"],
    "terraform": ["tf", "infrastructure as code", "iac"],
    "agile": ["scrum", "kanban"],
}


def normalize_skill(skill: str) -> str:
    """Normalize a skill name for comparison."""
    return skill.lower().strip().replace("-", " ").replace("_", " ")


def get_skill_variations(skill: str) -> set[str]:
    """Get all variations/synonyms of a skill."""
    normalized = normalize_skill(skill)
    variations = {normalized}

    # Check if this skill is a key in synonyms
    if normalized in SKILL_SYNONYMS:
        variations.update(SKILL_SYNONYMS[normalized])

    # Check if this skill is a value in synonyms
    for key, synonyms in SKILL_SYNONYMS.items():
        if normalized in synonyms or normalized == key:
            variations.add(key)
            variations.update(synonyms)

    return variations


def skills_match(skill1: str, skill2: str) -> tuple[bool, str]:
    """
    Check if two skills match (exact, partial, or synonym).

    Returns:
        Tuple of (is_match, match_type)
    """
    s1 = normalize_skill(skill1)
    s2 = normalize_skill(skill2)

    # Exact match
    if s1 == s2:
        return True, "exact"

    # Partial match (one contains the other)
    if s1 in s2 or s2 in s1:
        return True, "partial"

    # Synonym match
    variations1 = get_skill_variations(skill1)
    variations2 = get_skill_variations(skill2)

    if variations1 & variations2:  # Intersection
        return True, "synonym"

    return False, "none"


@dataclass
class ATSAnalyzer:
    """Analyzes resume against job description for ATS compatibility."""

    def calculate_ats_score(
        self,
        resume_data: dict[str, Any],
        jd_data: dict[str, Any],
    ) -> ATSScoreResult:
        """
        Calculate ATS compatibility score.

        Args:
            resume_data: Extracted resume data
            jd_data: Extracted job description data

        Returns:
            ATSScoreResult with scores and analysis
        """
        logger.processing("ATS score calculation")

        # Extract skills from resume
        resume_skills = set()
        for skill in resume_data.get("skills", []):
            resume_skills.add(normalize_skill(skill))
        for skill in resume_data.get("technical_skills", []):
            resume_skills.add(normalize_skill(skill))

        # Also extract skills mentioned in experience highlights
        for exp in resume_data.get("experience", []):
            for highlight in exp.get("highlights", []):
                # Simple extraction of capitalized words that might be skills
                words = re.findall(r"\b[A-Z][a-zA-Z+#]+\b", highlight)
                for word in words:
                    if len(word) > 1:
                        resume_skills.add(normalize_skill(word))

        # Get JD requirements
        required_skills = [
            normalize_skill(s) for s in jd_data.get("required_skills", [])
        ]
        preferred_skills = [
            normalize_skill(s) for s in jd_data.get("preferred_skills", [])
        ]
        all_keywords = [normalize_skill(k) for k in jd_data.get("keywords", [])]

        # Calculate skill matches
        skill_matches = []
        matched_required = []
        missing_required = []
        matched_preferred = []
        missing_preferred = []
        matched_keywords = []
        missing_keywords = []

        # Check required skills
        for req_skill in required_skills:
            found = False
            match_type = "none"
            evidence = None

            for resume_skill in resume_skills:
                is_match, m_type = skills_match(req_skill, resume_skill)
                if is_match:
                    found = True
                    match_type = m_type
                    evidence = resume_skill
                    break

            skill_matches.append(
                SkillMatch(
                    skill=req_skill,
                    found_in_resume=found,
                    match_type=match_type if found else "none",
                    resume_evidence=evidence,
                )
            )

            if found:
                matched_required.append(req_skill)
            else:
                missing_required.append(req_skill)

        # Check preferred skills
        for pref_skill in preferred_skills:
            found = False
            for resume_skill in resume_skills:
                is_match, _ = skills_match(pref_skill, resume_skill)
                if is_match:
                    found = True
                    break

            if found:
                matched_preferred.append(pref_skill)
            else:
                missing_preferred.append(pref_skill)

        # Check keywords
        resume_text = self._get_resume_text(resume_data).lower()
        for keyword in all_keywords:
            if keyword in resume_text or any(
                v in resume_text for v in get_skill_variations(keyword)
            ):
                matched_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)

        # Calculate scores
        # Skills score: Required (70%) + Preferred (30%)
        if required_skills:
            required_score = (len(matched_required) / len(required_skills)) * 70
        else:
            required_score = 70  # No requirements = full score

        if preferred_skills:
            preferred_score = (len(matched_preferred) / len(preferred_skills)) * 30
        else:
            preferred_score = 30

        skills_match_score = int(required_score + preferred_score)

        # Keyword score
        if all_keywords:
            keyword_match_score = int((len(matched_keywords) / len(all_keywords)) * 100)
        else:
            keyword_match_score = 100

        # Experience score
        experience_match_score = self._calculate_experience_score(resume_data, jd_data)

        # Education score
        education_match_score = self._calculate_education_score(resume_data, jd_data)

        # Overall ATS score (weighted)
        # Skills: 40%, Keywords: 25%, Experience: 25%, Education: 10%
        ats_score = int(
            skills_match_score * 0.40
            + keyword_match_score * 0.25
            + experience_match_score * 0.25
            + education_match_score * 0.10
        )

        # Generate suggestions
        suggestions = self._generate_suggestions(
            missing_required,
            missing_preferred,
            missing_keywords,
            experience_match_score,
            education_match_score,
            resume_data,
            jd_data,
        )

        # Generate summary
        summary = self._generate_summary(
            ats_score,
            len(matched_required),
            len(required_skills),
            len(missing_required),
        )

        logger.success(f"ATS score: {ats_score}/100")

        return ATSScoreResult(
            ats_score=ats_score,
            keyword_match_score=keyword_match_score,
            skills_match_score=skills_match_score,
            experience_match_score=experience_match_score,
            education_match_score=education_match_score,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords[:10],  # Top 10
            matched_skills=matched_required + matched_preferred,
            missing_required_skills=missing_required,
            missing_preferred_skills=missing_preferred,
            skill_matches=skill_matches,
            suggestions=suggestions,
            summary=summary,
        )

    def _get_resume_text(self, resume_data: dict[str, Any]) -> str:
        """Combine all resume text for keyword searching."""
        parts = []

        # Add summary
        if resume_data.get("summary"):
            parts.append(resume_data["summary"])

        # Add skills
        parts.extend(resume_data.get("skills") or [])
        parts.extend(resume_data.get("technical_skills") or [])

        # Add experience
        for exp in resume_data.get("experience") or []:
            parts.append(exp.get("role", ""))
            parts.append(exp.get("company", ""))
            parts.extend(exp.get("highlights") or [])

        # Add education
        for edu in resume_data.get("education") or []:
            parts.append(edu.get("degree", ""))
            parts.append(edu.get("field_of_study", ""))
            parts.append(edu.get("institution", ""))

        # Add certifications
        parts.extend(resume_data.get("certifications") or [])

        # Add projects
        for proj in resume_data.get("projects") or []:
            parts.append(proj.get("name", ""))
            parts.append(proj.get("description", ""))
            parts.extend(proj.get("technologies") or [])

        return " ".join(str(p) for p in parts if p)

    def _calculate_experience_score(
        self,
        resume_data: dict[str, Any],
        jd_data: dict[str, Any],
    ) -> int:
        """Calculate experience match score."""
        resume_years = resume_data.get("total_experience_years", 0) or 0

        min_years = jd_data.get("experience_years_min")
        max_years = jd_data.get("experience_years_max")

        if min_years is None and max_years is None:
            return 100  # No requirement

        if min_years is None:
            min_years = 0
        if max_years is None:
            max_years = min_years + 10

        if resume_years >= min_years:
            if resume_years <= max_years:
                return 100  # Perfect match
            else:
                # Overqualified - slight penalty
                over = resume_years - max_years
                return max(60, 100 - int(over * 5))
        else:
            # Under-qualified
            under = min_years - resume_years
            if under <= 1:
                return 70  # Close enough
            elif under <= 2:
                return 50
            else:
                return max(20, 50 - int(under * 10))

    def _calculate_education_score(
        self,
        resume_data: dict[str, Any],
        jd_data: dict[str, Any],
    ) -> int:
        """Calculate education match score."""
        required_edu = jd_data.get("required_education", "").lower()

        if not required_edu:
            return 100  # No requirement

        resume_education = resume_data.get("education", [])
        if not resume_education:
            return 30  # No education listed

        # Check highest degree
        degrees = []
        for edu in resume_education:
            degree = edu.get("degree", "").lower()
            degrees.append(degree)

        # Simple matching
        degree_levels = {
            "phd": 5,
            "doctorate": 5,
            "ph.d": 5,
            "master": 4,
            "msc": 4,
            "mba": 4,
            "ms": 4,
            "bachelor": 3,
            "bsc": 3,
            "ba": 3,
            "bs": 3,
            "associate": 2,
            "diploma": 1,
            "certificate": 1,
        }

        # Find required level
        req_level = 0
        for key, level in degree_levels.items():
            if key in required_edu:
                req_level = level
                break

        # Find candidate's highest level
        candidate_level = 0
        for degree in degrees:
            for key, level in degree_levels.items():
                if key in degree:
                    candidate_level = max(candidate_level, level)

        if candidate_level >= req_level:
            return 100
        elif candidate_level == req_level - 1:
            return 70
        else:
            return 40

    def _generate_suggestions(
        self,
        missing_required: list[str],
        missing_preferred: list[str],
        missing_keywords: list[str],
        experience_score: int,
        education_score: int,
        resume_data: dict[str, Any],
        jd_data: dict[str, Any],
    ) -> list[str]:
        """Generate improvement suggestions."""
        suggestions = []

        # Missing required skills
        if missing_required:
            top_missing = missing_required[:5]
            suggestions.append(
                f"Add these required skills if you have experience: {', '.join(top_missing)}"
            )

        # Missing preferred skills
        if missing_preferred and len(missing_preferred) > len(missing_required):
            top_missing = [
                s for s in missing_preferred[:3] if s not in missing_required
            ]
            if top_missing:
                suggestions.append(
                    f"Consider highlighting these preferred skills: {', '.join(top_missing)}"
                )

        # Missing keywords
        if missing_keywords:
            unique_keywords = [
                k
                for k in missing_keywords[:5]
                if k not in missing_required and k not in missing_preferred
            ]
            if unique_keywords:
                suggestions.append(
                    f"Include these keywords in your resume: {', '.join(unique_keywords)}"
                )

        # Experience gap
        if experience_score < 70:
            suggestions.append(
                "Highlight relevant projects or freelance work to bridge experience gap"
            )

        # Education gap
        if education_score < 70:
            suggestions.append(
                "List relevant certifications or courses to strengthen education section"
            )

        # Generic suggestions
        if not resume_data.get("summary"):
            suggestions.append(
                "Add a professional summary highlighting your fit for this role"
            )

        certifications = resume_data.get("certifications") or []
        jd_certs = (jd_data.get("required_certifications") or []) + (
            jd_data.get("preferred_certifications") or []
        )
        if jd_certs and not certifications:
            suggestions.append(
                f"Consider obtaining relevant certifications: {', '.join(jd_certs[:3])}"
            )

        return suggestions[:7]  # Max 7 suggestions

    def _generate_summary(
        self,
        ats_score: int,
        matched_required: int,
        total_required: int,
        missing_required_count: int,
    ) -> str:
        """Generate a summary explanation of the ATS score."""
        if ats_score >= 90:
            grade = "Excellent"
            detail = "This resume is highly optimized for this job posting."
        elif ats_score >= 75:
            grade = "Good"
            detail = "Strong match with room for minor improvements."
        elif ats_score >= 60:
            grade = "Fair"
            detail = "Moderate match - consider adding missing keywords."
        elif ats_score >= 40:
            grade = "Needs Work"
            detail = "Significant gaps in required skills or keywords."
        else:
            grade = "Poor Match"
            detail = "Major mismatch - this role may not be a good fit."

        if total_required > 0:
            skill_info = (
                f" Matched {matched_required}/{total_required} required skills."
            )
        else:
            skill_info = ""

        return f"{grade} ({ats_score}/100). {detail}{skill_info}"


# Singleton instance
_ats_analyzer: ATSAnalyzer | None = None


def get_ats_analyzer() -> ATSAnalyzer:
    """Get the singleton ATS analyzer instance."""
    global _ats_analyzer
    if _ats_analyzer is None:
        _ats_analyzer = ATSAnalyzer()
    return _ats_analyzer
