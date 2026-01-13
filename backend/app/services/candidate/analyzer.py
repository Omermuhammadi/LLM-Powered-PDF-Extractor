"""
Candidate analysis service.

Provides fit scoring, red flag detection, and career analysis.
"""

from dataclasses import dataclass
from typing import Any

from app.core import logger
from app.schemas.candidate import (
    CandidateFitResult,
    CareerProgression,
    FitScoreBreakdown,
    RecommendationType,
    RedFlag,
    RedFlagSeverity,
    RedFlagType,
    StrengthItem,
)
from app.services.llm import get_llm_client
from app.services.llm.parser import parse_llm_response

# Prompt for fit scoring and red flag detection
FIT_ANALYSIS_SYSTEM_PROMPT = """You are an expert HR analyst and recruiter with 20+ years of experience screening candidates. You analyze resumes against job descriptions to provide actionable insights.

Your job is to:
1. Calculate a FIT SCORE (0-100) based on how well the candidate matches the job
2. Detect RED FLAGS that recruiters should investigate
3. Identify STRENGTHS that make this candidate stand out
4. Provide a clear RECOMMENDATION

SCORING CRITERIA:
- Skills Alignment (0-100): How well do their skills match required/preferred skills?
- Experience Match (0-100): Do they have the right level and type of experience?
- Education Fit (0-100): Does their education meet requirements?
- Career Trajectory (0-100): Is their career progressing appropriately?
- Cultural Signals (0-100): Any indicators of cultural fit (leadership, teamwork, etc.)?

RED FLAG DETECTION - Be thorough:
1. SHORT_TENURE: Multiple jobs <1 year (excluding internships/contracts)
2. EMPLOYMENT_GAP: Gaps >6 months without explanation
3. OVERQUALIFIED: Way more experience than needed (may leave quickly)
4. UNDERQUALIFIED: Significantly less experience than required
5. FREQUENT_JOB_CHANGES: 4+ jobs in 5 years (job hopper pattern)
6. CAREER_REGRESSION: Moving from senior to junior roles
7. OVERLAPPING_JOBS: Dates that don't make sense
8. NO_PROGRESSION: Same role/level for 5+ years
9. SKILL_GAPS: Missing critical required skills

RECOMMENDATION CATEGORIES:
- STRONG_HIRE: Score 85+, no critical red flags, excellent match
- GOOD_FIT: Score 70-84, minor concerns, worth interviewing
- POTENTIAL_FIT: Score 55-69, some gaps but potential
- NEEDS_REVIEW: Score 40-54, significant concerns
- NOT_RECOMMENDED: Score <40 or critical red flags

Be honest, specific, and actionable. Recruiters depend on your analysis."""


FIT_ANALYSIS_USER_TEMPLATE = """Analyze this candidate for the job and provide a comprehensive assessment.

JOB REQUIREMENTS:
{jd_summary}

CANDIDATE PROFILE:
- Name: {candidate_name}
- Current Role: {current_role} at {current_company}
- Total Experience: {experience_years} years
- Location: {location}

SKILLS:
{skills}

WORK EXPERIENCE:
{experience}

EDUCATION:
{education}

CERTIFICATIONS:
{certifications}

Return ONLY this JSON structure:
{{
  "fit_score": 75,
  "fit_score_breakdown": {{
    "skills_alignment": 80,
    "experience_match": 70,
    "education_fit": 85,
    "career_trajectory": 75,
    "cultural_signals": 65
  }},
  "recommendation": "GOOD_FIT",
  "recommendation_text": "Strong technical match with 7 years of relevant experience. Minor concern about job tenure pattern. Worth interviewing.",
  "strengths": [
    {{
      "category": "skills",
      "title": "Strong Python & ML expertise",
      "description": "8+ years of Python with TensorFlow and PyTorch",
      "relevance_score": 95
    }}
  ],
  "weaknesses": [
    "Limited cloud experience (only 1 year with AWS)",
    "No leadership experience mentioned"
  ],
  "red_flags": [
    {{
      "flag_type": "SHORT_TENURE",
      "severity": "medium",
      "title": "Short tenure at previous company",
      "description": "Only 8 months at TechCorp before moving",
      "evidence": "TechCorp: Mar 2023 - Nov 2023",
      "suggestion": "Ask about reason for leaving TechCorp"
    }}
  ],
  "career_progression": {{
    "trajectory": "upward",
    "avg_tenure_months": 24,
    "longest_tenure_months": 48,
    "total_companies": 4,
    "has_leadership_progression": true,
    "progression_summary": "Steady growth from Junior to Senior Developer over 7 years"
  }},
  "executive_summary": "A strong candidate with solid technical skills and progressive career growth. The 8-month stint at TechCorp warrants discussion, but overall experience aligns well with the Senior Data Scientist role. Recommend proceeding to technical interview.",
  "interview_questions": [
    "Why did you leave TechCorp after only 8 months?",
    "Describe a project where you led a team",
    "How have you used Docker in production?"
  ],
  "suggested_level": "Senior"
}}

Be specific with evidence from the resume. Do NOT invent information."""


def format_experience_for_prompt(experience: list[dict]) -> str:
    """Format experience entries for the prompt."""
    if not experience:
        return "No experience listed"

    lines = []
    for i, exp in enumerate(experience, 1):
        company = exp.get("company", "Unknown")
        role = exp.get("role", "Unknown")
        duration = exp.get("duration", "Unknown")
        months = exp.get("duration_months", "?")
        highlights = exp.get("highlights", [])

        lines.append(f"{i}. {role} at {company}")
        lines.append(f"   Duration: {duration} ({months} months)")
        if highlights:
            for h in highlights[:3]:  # Limit highlights
                lines.append(f"   • {h}")

    return "\n".join(lines)


def format_education_for_prompt(education: list[dict]) -> str:
    """Format education entries for the prompt."""
    if not education:
        return "No education listed"

    lines = []
    for edu in education:
        degree = edu.get("degree", "Degree")
        field = edu.get("field_of_study", "")
        institution = edu.get("institution", "Unknown")
        year = edu.get("year", "")
        gpa = edu.get("gpa")

        line = f"• {degree}"
        if field:
            line += f" in {field}"
        line += f" - {institution}"
        if year:
            line += f" ({year})"
        if gpa:
            line += f" - GPA: {gpa}"
        lines.append(line)

    return "\n".join(lines)


def format_jd_for_prompt(jd_data: dict) -> str:
    """Format JD data for the prompt."""
    parts = []

    if jd_data.get("job_title"):
        parts.append(f"Position: {jd_data['job_title']}")

    if jd_data.get("company_name"):
        parts.append(f"Company: {jd_data['company_name']}")

    exp_req = jd_data.get("experience_required") or jd_data.get("experience_years_min")
    if exp_req:
        parts.append(f"Experience: {exp_req}")

    required = jd_data.get("required_skills", [])
    if required:
        parts.append(f"Required Skills: {', '.join(required)}")

    preferred = jd_data.get("preferred_skills", [])
    if preferred:
        parts.append(f"Preferred Skills: {', '.join(preferred)}")

    education = jd_data.get("required_education")
    if education:
        parts.append(f"Education: {education}")

    return "\n".join(parts) if parts else "No specific requirements provided"


@dataclass
class CandidateAnalyzer:
    """Analyzes candidates for fit scoring and red flag detection."""

    def analyze_candidate(
        self,
        resume_data: dict[str, Any],
        jd_data: dict[str, Any],
    ) -> CandidateFitResult:
        """
        Perform comprehensive candidate analysis.

        Args:
            resume_data: Extracted resume data
            jd_data: Extracted job description data

        Returns:
            CandidateFitResult with scores, red flags, and recommendation
        """
        logger.processing("candidate fit analysis")

        # First, do rule-based red flag detection
        rule_based_flags = self._detect_red_flags_rules(resume_data)

        # Then, use LLM for comprehensive analysis
        llm_result = self._analyze_with_llm(resume_data, jd_data)

        # Merge rule-based and LLM-detected flags
        if llm_result:
            # Add any rule-based flags not detected by LLM
            existing_types = {f.flag_type for f in llm_result.red_flags}
            for flag in rule_based_flags:
                if flag.flag_type not in existing_types:
                    llm_result.red_flags.append(flag)

            # Update counts
            llm_result.red_flag_count = len(llm_result.red_flags)
            llm_result.has_critical_red_flags = any(
                f.severity == RedFlagSeverity.HIGH for f in llm_result.red_flags
            )

            logger.success(
                f"Fit score: {llm_result.fit_score}/100, Red flags: {llm_result.red_flag_count}"
            )
            return llm_result

        # Fallback to rule-based only
        return self._create_fallback_result(resume_data, jd_data, rule_based_flags)

    def _detect_red_flags_rules(self, resume_data: dict[str, Any]) -> list[RedFlag]:
        """Detect red flags using rule-based logic."""
        flags = []
        experience = resume_data.get("experience") or []

        if not experience:
            return flags

        # Check for short tenures
        short_tenure_count = 0
        for exp in experience:
            months = exp.get("duration_months", 0) or 0
            is_current = exp.get("is_current", False)

            # Skip if current job or internship
            role = (exp.get("role") or "").lower()
            if is_current or "intern" in role:
                continue

            if 0 < months < 12:
                short_tenure_count += 1

        if short_tenure_count >= 2:
            flags.append(
                RedFlag(
                    flag_type=RedFlagType.SHORT_TENURE,
                    severity=(
                        RedFlagSeverity.MEDIUM
                        if short_tenure_count == 2
                        else RedFlagSeverity.HIGH
                    ),
                    title=f"{short_tenure_count} jobs with tenure < 1 year",
                    description=f"Candidate has {short_tenure_count} positions with less than 12 months tenure",
                    evidence=None,
                    suggestion="Ask about reasons for leaving each short-tenure position",
                )
            )

        # Check for frequent job changes
        non_current_jobs = [e for e in experience if not e.get("is_current", False)]
        if len(non_current_jobs) >= 4:
            # Calculate average tenure
            total_months = sum(
                e.get("duration_months", 0) or 0 for e in non_current_jobs
            )
            avg_months = total_months / len(non_current_jobs) if non_current_jobs else 0

            if avg_months < 18:
                flags.append(
                    RedFlag(
                        flag_type=RedFlagType.FREQUENT_JOB_CHANGES,
                        severity=RedFlagSeverity.MEDIUM,
                        title="Frequent job changes pattern",
                        description=f"Average tenure of {avg_months:.0f} months across {len(non_current_jobs)} positions",
                        evidence=None,
                        suggestion="Discuss career goals and what they're looking for in next role",
                    )
                )

        # Check for no recent experience
        if experience:
            most_recent = experience[0]
            if not most_recent.get("is_current", False):
                end_date = most_recent.get("end_date", "")
                if end_date and end_date != "Present":
                    # Simple check - if end_date is older than 6 months
                    try:
                        if (
                            "2024" not in end_date
                            and "2025" not in end_date
                            and "2026" not in end_date
                        ):
                            flags.append(
                                RedFlag(
                                    flag_type=RedFlagType.EMPLOYMENT_GAP,
                                    severity=RedFlagSeverity.MEDIUM,
                                    title="Possible employment gap",
                                    description="Most recent position may have ended some time ago",
                                    evidence=f"Last position ended: {end_date}",
                                    suggestion="Ask about activities since last position",
                                )
                            )
                    except Exception:
                        pass

        return flags

    def _analyze_with_llm(
        self,
        resume_data: dict[str, Any],
        jd_data: dict[str, Any],
    ) -> CandidateFitResult | None:
        """Use LLM for comprehensive candidate analysis."""
        try:
            llm = get_llm_client()

            # Format prompt
            user_prompt = FIT_ANALYSIS_USER_TEMPLATE.format(
                jd_summary=format_jd_for_prompt(jd_data),
                candidate_name=resume_data.get("candidate_name", "Unknown"),
                current_role=resume_data.get("current_role", "Not specified"),
                current_company=resume_data.get("current_company", "Not specified"),
                experience_years=resume_data.get("total_experience_years", "Unknown"),
                location=resume_data.get("location", "Not specified"),
                skills=", ".join(resume_data.get("skills", [])[:20]) or "None listed",
                experience=format_experience_for_prompt(
                    resume_data.get("experience", [])
                ),
                education=format_education_for_prompt(resume_data.get("education", [])),
                certifications=", ".join(resume_data.get("certifications", [])[:10])
                or "None listed",
            )

            # Call LLM
            response = llm.generate_sync(
                prompt=user_prompt,
                system=FIT_ANALYSIS_SYSTEM_PROMPT,
                temperature=0.2,
                json_mode=True,
            )

            # Parse response
            parse_result = parse_llm_response(response.content)

            if not parse_result.success:
                logger.warning(f"Failed to parse fit analysis: {parse_result.error}")
                return None

            data = parse_result.data

            # Build result
            return self._build_result_from_llm(data)

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return None

    def _build_result_from_llm(self, data: dict) -> CandidateFitResult:
        """Build CandidateFitResult from LLM response."""
        # Parse red flags
        red_flags = []
        for rf in data.get("red_flags", []):
            try:
                flag_type = rf.get("flag_type", "OTHER").upper()
                if flag_type not in [e.value.upper() for e in RedFlagType]:
                    flag_type = "OTHER"

                severity = rf.get("severity", "medium").lower()
                if severity not in ["high", "medium", "low"]:
                    severity = "medium"

                red_flags.append(
                    RedFlag(
                        flag_type=RedFlagType(flag_type.lower()),
                        severity=RedFlagSeverity(severity),
                        title=rf.get("title", "Unspecified flag"),
                        description=rf.get("description", ""),
                        evidence=rf.get("evidence"),
                        suggestion=rf.get("suggestion"),
                    )
                )
            except Exception:
                continue

        # Parse strengths
        strengths = []
        for s in data.get("strengths", []):
            try:
                strengths.append(
                    StrengthItem(
                        category=s.get("category", "general"),
                        title=s.get("title", ""),
                        description=s.get("description", ""),
                        relevance_score=s.get("relevance_score", 80),
                    )
                )
            except Exception:
                continue

        # Parse career progression
        career_prog = None
        cp_data = data.get("career_progression")
        if cp_data:
            try:
                career_prog = CareerProgression(
                    trajectory=cp_data.get("trajectory", "mixed"),
                    avg_tenure_months=cp_data.get("avg_tenure_months", 0),
                    longest_tenure_months=cp_data.get("longest_tenure_months", 0),
                    total_companies=cp_data.get("total_companies", 0),
                    has_leadership_progression=cp_data.get(
                        "has_leadership_progression", False
                    ),
                    progression_summary=cp_data.get("progression_summary", ""),
                )
            except Exception:
                pass

        # Parse score breakdown
        breakdown = None
        bd_data = data.get("fit_score_breakdown")
        if bd_data:
            try:
                breakdown = FitScoreBreakdown(
                    skills_alignment=bd_data.get("skills_alignment", 70),
                    experience_match=bd_data.get("experience_match", 70),
                    education_fit=bd_data.get("education_fit", 70),
                    career_trajectory=bd_data.get("career_trajectory", 70),
                    cultural_signals=bd_data.get("cultural_signals", 70),
                )
            except Exception:
                pass

        # Parse recommendation
        rec_str = data.get("recommendation", "NEEDS_REVIEW").upper()
        rec_map = {
            "STRONG_HIRE": RecommendationType.STRONG_HIRE,
            "GOOD_FIT": RecommendationType.GOOD_FIT,
            "POTENTIAL_FIT": RecommendationType.POTENTIAL_FIT,
            "NEEDS_REVIEW": RecommendationType.NEEDS_REVIEW,
            "NOT_RECOMMENDED": RecommendationType.NOT_RECOMMENDED,
        }
        recommendation = rec_map.get(rec_str, RecommendationType.NEEDS_REVIEW)

        return CandidateFitResult(
            fit_score=data.get("fit_score", 50),
            fit_score_breakdown=breakdown,
            recommendation=recommendation,
            recommendation_text=data.get("recommendation_text", ""),
            strengths=strengths,
            weaknesses=data.get("weaknesses", []),
            red_flags=red_flags,
            red_flag_count=len(red_flags),
            has_critical_red_flags=any(
                f.severity == RedFlagSeverity.HIGH for f in red_flags
            ),
            career_progression=career_prog,
            executive_summary=data.get("executive_summary", ""),
            interview_questions=data.get("interview_questions", []),
            suggested_level=data.get("suggested_level"),
            analysis_confidence=0.85,
        )

    def _create_fallback_result(
        self,
        resume_data: dict[str, Any],
        jd_data: dict[str, Any],
        red_flags: list[RedFlag],
    ) -> CandidateFitResult:
        """Create a fallback result when LLM fails."""
        # Simple heuristic-based scoring
        score = 50

        # Adjust based on experience
        years = resume_data.get("total_experience_years", 0) or 0
        min_years = jd_data.get("experience_years_min", 0) or 0

        if years >= min_years:
            score += 15
        elif years >= min_years * 0.7:
            score += 5
        else:
            score -= 10

        # Adjust based on skills
        skills = set(s.lower() for s in (resume_data.get("skills") or []))
        required = set(s.lower() for s in (jd_data.get("required_skills") or []))

        if required:
            overlap = len(skills & required) / len(required)
            score += int(overlap * 20)

        # Adjust based on red flags
        score -= len(red_flags) * 5
        score = max(0, min(100, score))

        # Determine recommendation
        if score >= 70:
            rec = RecommendationType.GOOD_FIT
            rec_text = "Candidate shows potential based on available data"
        elif score >= 50:
            rec = RecommendationType.POTENTIAL_FIT
            rec_text = "Some gaps identified, further review recommended"
        else:
            rec = RecommendationType.NEEDS_REVIEW
            rec_text = "Significant gaps, careful evaluation needed"

        return CandidateFitResult(
            fit_score=score,
            recommendation=rec,
            recommendation_text=rec_text,
            red_flags=red_flags,
            red_flag_count=len(red_flags),
            has_critical_red_flags=any(
                f.severity == RedFlagSeverity.HIGH for f in red_flags
            ),
            executive_summary="Analysis performed with limited LLM support. Manual review recommended.",
            analysis_confidence=0.5,
        )


# Singleton instance
_candidate_analyzer: CandidateAnalyzer | None = None


def get_candidate_analyzer() -> CandidateAnalyzer:
    """Get the singleton candidate analyzer instance."""
    global _candidate_analyzer
    if _candidate_analyzer is None:
        _candidate_analyzer = CandidateAnalyzer()
    return _candidate_analyzer
