"""
Candidate ranking and comparison service.

Provides multi-resume ranking, comparison, and side-by-side analysis.
"""

from app.core import logger
from app.schemas.candidate import (
    CandidateComparison,
    CandidateRankingScore,
    FullCandidateAnalysis,
    RankingResult,
    RecommendationType,
)


class CandidateRanker:
    """Ranks and compares multiple candidates for a job."""

    @staticmethod
    def rank_candidates(
        analyses: dict[str, FullCandidateAnalysis],
        job_title: str | None = None,
        company_name: str | None = None,
    ) -> RankingResult:
        """
        Rank multiple candidates based on their analyses.

        Args:
            analyses: Dict mapping file names to FullCandidateAnalysis results
            job_title: Title of the job position
            company_name: Name of the company

        Returns:
            RankingResult with ranked candidates and insights
        """
        logger.processing("candidate ranking")

        if not analyses:
            return RankingResult(
                success=False, rankings=[], error="No candidates provided"
            )

        # Create ranking scores for each candidate
        ranking_scores: list[CandidateRankingScore] = []

        for file_name, analysis in analyses.items():
            score = CandidateRankingScore(
                rank=0,  # Will be set after sorting
                file_name=file_name,
                candidate_name=analysis.candidate_name,
                overall_score=analysis.overall_score,
                ats_score=analysis.ats_score,
                fit_score=(
                    analysis.fit_analysis.fit_score if analysis.fit_analysis else 0
                ),
                recommendation=(
                    analysis.fit_analysis.recommendation
                    if analysis.fit_analysis
                    else RecommendationType.NEEDS_REVIEW
                ),
                strengths_count=(
                    len(analysis.fit_analysis.strengths) if analysis.fit_analysis else 0
                ),
                red_flags_count=(
                    analysis.fit_analysis.red_flag_count if analysis.fit_analysis else 0
                ),
                has_critical_red_flags=(
                    analysis.fit_analysis.has_critical_red_flags
                    if analysis.fit_analysis
                    else False
                ),
                suggested_level=(
                    analysis.fit_analysis.suggested_level
                    if analysis.fit_analysis
                    else None
                ),
                executive_summary=(
                    analysis.fit_analysis.executive_summary
                    if analysis.fit_analysis
                    else None
                ),
            )
            ranking_scores.append(score)

        # Sort by overall_score (descending)
        ranking_scores.sort(key=lambda x: x.overall_score, reverse=True)

        # Update rank numbers
        for idx, score in enumerate(ranking_scores, 1):
            score.rank = idx

        # Calculate statistics
        total_score = sum(s.overall_score for s in ranking_scores)
        average_score = total_score / len(ranking_scores) if ranking_scores else 0

        # Score distribution
        score_dist = {
            "excellent": len([s for s in ranking_scores if s.overall_score >= 85]),
            "good": len([s for s in ranking_scores if 70 <= s.overall_score < 85]),
            "acceptable": len(
                [s for s in ranking_scores if 50 <= s.overall_score < 70]
            ),
            "poor": len([s for s in ranking_scores if s.overall_score < 50]),
        }

        # Get top candidate
        top_candidate = ranking_scores[0] if ranking_scores else None
        top_analysis = analyses.get(top_candidate.file_name) if top_candidate else None

        # Generate hiring recommendation
        hiring_rec = CandidateRanker._generate_hiring_recommendation(
            ranking_scores, score_dist
        )

        result = RankingResult(
            success=True,
            job_title=job_title,
            company_name=company_name,
            total_candidates=len(ranking_scores),
            rankings=ranking_scores,
            top_candidate=top_candidate,
            top_candidate_analysis=top_analysis,
            all_analyses=analyses,
            score_distribution=score_dist,
            average_score=average_score,
            hiring_recommendation=hiring_rec,
            processing_time_ms=0,
        )

        logger.success(f"Ranked {len(ranking_scores)} candidates")
        return result

    @staticmethod
    def _generate_hiring_recommendation(
        ranked: list[CandidateRankingScore], distribution: dict[str, int]
    ) -> str:
        """Generate overall hiring recommendation."""
        if not ranked:
            return "No candidates to evaluate."

        top_score = ranked[0].overall_score
        strong_hires = len([s for s in ranked if s.overall_score >= 85])
        top_name = ranked[0].candidate_name or ranked[0].file_name

        if top_score >= 85 and not ranked[0].has_critical_red_flags:
            return (
                f"✅ STRONG RECOMMENDATION: Top candidate ({top_name}) is an "
                f"excellent fit with {top_score}/100 score and no critical red flags."
            )
        elif strong_hires > 0:
            return (
                f"✅ GOOD POOL: {strong_hires} strong candidate(s) available. "
                f"Top score: {top_score}/100. Review red flags before proceeding."
            )
        elif top_score >= 70:
            return (
                f"⚠️ ACCEPTABLE: Top candidate at {top_score}/100. "
                f"Pool quality is moderate. Consider expanding search."
            )
        else:
            return (
                f"❌ WEAK POOL: Highest score is {top_score}/100. "
                f"Not recommended to proceed without additional candidates."
            )

    @staticmethod
    def compare_candidates(
        analysis_1: FullCandidateAnalysis,
        analysis_2: FullCandidateAnalysis,
        file_name_1: str,
        file_name_2: str,
    ) -> CandidateComparison:
        """
        Compare two candidates side-by-side.

        Args:
            analysis_1: First candidate analysis
            analysis_2: Second candidate analysis
            file_name_1: File name of first candidate
            file_name_2: File name of second candidate

        Returns:
            CandidateComparison with detailed comparison
        """
        logger.processing("candidate comparison")

        # Calculate skill differences
        skills_1 = set(analysis_1.matched_skills)
        skills_2 = set(analysis_2.matched_skills)
        unique_1 = list(skills_1 - skills_2)
        unique_2 = list(skills_2 - skills_1)
        common = list(skills_1 & skills_2)

        # Determine winner
        score_diff = analysis_1.overall_score - analysis_2.overall_score
        winner = 1 if score_diff > 0 else (2 if score_diff < 0 else 1)
        winner_reason = CandidateRanker._generate_comparison_reason(
            analysis_1, analysis_2, winner, score_diff
        )

        comparison = CandidateComparison(
            file_name_1=file_name_1,
            file_name_2=file_name_2,
            overall_score_1=analysis_1.overall_score,
            overall_score_2=analysis_2.overall_score,
            overall_score_diff=score_diff,
            ats_score_1=analysis_1.ats_score,
            ats_score_2=analysis_2.ats_score,
            fit_score_1=(
                analysis_1.fit_analysis.fit_score if analysis_1.fit_analysis else 0
            ),
            fit_score_2=(
                analysis_2.fit_analysis.fit_score if analysis_2.fit_analysis else 0
            ),
            matched_skills_1=analysis_1.matched_skills,
            matched_skills_2=analysis_2.matched_skills,
            unique_skills_1=unique_1,
            unique_skills_2=unique_2,
            common_skills=common,
            red_flags_1=(
                analysis_1.fit_analysis.red_flag_count if analysis_1.fit_analysis else 0
            ),
            red_flags_2=(
                analysis_2.fit_analysis.red_flag_count if analysis_2.fit_analysis else 0
            ),
            critical_flags_1=(
                analysis_1.fit_analysis.has_critical_red_flags
                if analysis_1.fit_analysis
                else False
            ),
            critical_flags_2=(
                analysis_2.fit_analysis.has_critical_red_flags
                if analysis_2.fit_analysis
                else False
            ),
            recommendation_1=(
                analysis_1.fit_analysis.recommendation
                if analysis_1.fit_analysis
                else RecommendationType.NEEDS_REVIEW
            ),
            recommendation_2=(
                analysis_2.fit_analysis.recommendation
                if analysis_2.fit_analysis
                else RecommendationType.NEEDS_REVIEW
            ),
            winner=winner,
            winner_reason=winner_reason,
        )

        logger.success("Comparison complete")
        return comparison

    @staticmethod
    def _generate_comparison_reason(
        analysis_1: FullCandidateAnalysis,
        analysis_2: FullCandidateAnalysis,
        winner: int,
        score_diff: int,
    ) -> str:
        """Generate reason why one candidate is better."""
        winner_analysis = analysis_1 if winner == 1 else analysis_2
        loser_analysis = analysis_2 if winner == 1 else analysis_1

        reasons = []

        # Score difference
        if abs(score_diff) >= 10:
            reasons.append(
                f"Significantly higher overall score (+{abs(score_diff)} points)"
            )

        # ATS difference
        ats_winner = analysis_1.ats_score if winner == 1 else analysis_2.ats_score
        ats_loser = analysis_2.ats_score if winner == 1 else analysis_1.ats_score
        if ats_winner > ats_loser:
            reasons.append(f"Better ATS keyword match ({ats_winner} vs {ats_loser})")

        # Red flags
        red_flags_winner = (
            winner_analysis.fit_analysis.red_flag_count
            if winner_analysis.fit_analysis
            else 0
        )
        red_flags_loser = (
            loser_analysis.fit_analysis.red_flag_count
            if loser_analysis.fit_analysis
            else 0
        )
        if red_flags_winner < red_flags_loser:
            reasons.append(f"Fewer red flags ({red_flags_winner} vs {red_flags_loser})")

        # Recommendation
        if winner_analysis.fit_analysis and loser_analysis.fit_analysis:
            if (
                winner_analysis.fit_analysis.recommendation.value
                > loser_analysis.fit_analysis.recommendation.value
            ):
                reasons.append(
                    f"Better recommendation: {winner_analysis.fit_analysis.recommendation.value}"
                )

        if not reasons:
            reasons.append("Overall better fit for the role")

        return ". ".join(reasons) + "."


def get_candidate_ranker() -> CandidateRanker:
    """Get candidate ranker instance."""
    return CandidateRanker()
