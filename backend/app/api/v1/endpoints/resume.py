"""
Resume analysis endpoints - ATS scoring, JD matching, and candidate fit analysis.

Provides endpoints for analyzing resumes against job descriptions.
"""

import asyncio
import time
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core import logger
from app.schemas.ats import ATSScoreResult, ResumeJDAnalysisResult
from app.schemas.candidate import (
    CandidateComparison,
    FullCandidateAnalysis,
    RankingResult,
)
from app.services.ats import get_ats_analyzer
from app.services.candidate import get_candidate_analyzer, get_candidate_ranker
from app.services.extraction import ExtractionOrchestrator
from app.services.llm import get_llm_client
from app.services.llm.parser import parse_llm_response
from app.services.llm.prompts import format_jd_extraction_prompt
from app.services.pdf import extract_text_from_pdf, process_text
from app.utils.file_handler import cleanup_temp_file, save_temp_file

router = APIRouter(prefix="/resume", tags=["resume"])


async def extract_jd_data(jd_text: str) -> dict[str, Any]:
    """
    Extract structured data from job description text using LLM.

    Args:
        jd_text: Raw job description text

    Returns:
        Extracted JD data as dictionary
    """
    logger.processing("job description extraction")

    # Get LLM client
    llm = get_llm_client()

    # Format prompt
    system_prompt, user_prompt = format_jd_extraction_prompt(jd_text)

    # Call LLM (using generate_sync for simplicity)
    response = llm.generate_sync(
        prompt=user_prompt,
        system=system_prompt,
        json_mode=True,
    )

    # Parse response
    parse_result = parse_llm_response(response.content)

    if not parse_result.success:
        logger.warning(f"JD parsing failed: {parse_result.error}")
        return {}

    logger.success("JD extraction complete")
    return parse_result.data


@router.post(
    "/analyze-with-jd",
    response_model=ResumeJDAnalysisResult,
    summary="Analyze resume against job description",
    description="""
    Upload a resume PDF and provide a job description to get:
    - ATS compatibility score (0-100)
    - Matched and missing keywords
    - Skill gap analysis
    - Improvement suggestions

    You can provide the job description as:
    - Text in the `job_description_text` field
    - A PDF file in the `job_description_file` field
    """,
)
async def analyze_resume_with_jd(
    resume_file: Annotated[UploadFile, File(description="Resume PDF file")],
    job_description_text: Annotated[
        str | None, Form(description="Job description as plain text")
    ] = None,
    job_description_file: Annotated[
        UploadFile | None, File(description="Job description as PDF file")
    ] = None,
) -> ResumeJDAnalysisResult:
    """
    Analyze a resume against a job description.

    Returns ATS score, matched/missing skills, and suggestions.
    """
    start_time = time.time()

    # Validate inputs
    if not job_description_text and not job_description_file:
        raise HTTPException(
            status_code=400,
            detail="Either job_description_text or job_description_file is required",
        )

    if not resume_file.filename or not resume_file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Resume must be a PDF file",
        )

    temp_resume_path: Path | None = None
    temp_jd_path: Path | None = None

    try:
        # Save resume to temp file
        resume_content = await resume_file.read()
        temp_resume_path = save_temp_file(resume_content, resume_file.filename)

        # Extract resume data
        logger.processing(f"resume analysis: {resume_file.filename}")
        orchestrator = ExtractionOrchestrator()
        resume_result = orchestrator.extract_from_pdf(temp_resume_path)

        if not resume_result.success:
            return ResumeJDAnalysisResult(
                success=False,
                error=f"Resume extraction failed: {resume_result.error}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )

        resume_data = resume_result.extracted_fields

        # Get JD text
        if job_description_file and job_description_file.filename:
            # Extract from PDF
            jd_content = await job_description_file.read()
            temp_jd_path = save_temp_file(jd_content, job_description_file.filename)

            if job_description_file.filename.lower().endswith(".pdf"):
                jd_pdf_result = extract_text_from_pdf(temp_jd_path)
                jd_text = jd_pdf_result.text
            else:
                # Assume text file
                jd_text = jd_content.decode("utf-8", errors="ignore")
        else:
            jd_text = job_description_text or ""

        # Process JD text
        jd_processed = process_text(jd_text)

        # Extract JD data using LLM
        jd_data = await extract_jd_data(jd_processed.cleaned_text)

        # Calculate ATS score
        ats_analyzer = get_ats_analyzer()
        ats_result = ats_analyzer.calculate_ats_score(resume_data, jd_data)

        processing_time = (time.time() - start_time) * 1000

        logger.success(
            f"Resume analysis complete: ATS score {ats_result.ats_score}/100 "
            f"({processing_time:.0f}ms)"
        )

        return ResumeJDAnalysisResult(
            success=True,
            candidate_name=resume_data.get("candidate_name"),
            candidate_email=resume_data.get("email"),
            candidate_current_role=resume_data.get("current_role"),
            candidate_experience_years=resume_data.get("total_experience_years"),
            job_title=jd_data.get("job_title"),
            company_name=jd_data.get("company_name"),
            ats_result=ats_result,
            resume_data=resume_data,
            jd_data=jd_data,
            processing_time_ms=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume analysis failed: {e}")
        return ResumeJDAnalysisResult(
            success=False,
            error=str(e),
            processing_time_ms=(time.time() - start_time) * 1000,
        )
    finally:
        # Cleanup temp files
        if temp_resume_path:
            cleanup_temp_file(temp_resume_path)
        if temp_jd_path:
            cleanup_temp_file(temp_jd_path)


@router.post(
    "/quick-ats-score",
    response_model=ATSScoreResult,
    summary="Quick ATS score from text",
    description="Calculate ATS score from resume text and JD text (no file upload).",
)
async def quick_ats_score(
    resume_text: Annotated[str, Form(description="Resume text content")],
    job_description_text: Annotated[str, Form(description="Job description text")],
) -> ATSScoreResult:
    """
    Quick ATS scoring from text inputs (no file upload needed).

    Useful for testing or when text is already extracted.
    """
    logger.processing("quick ATS score calculation")

    try:
        # Extract resume data
        orchestrator = ExtractionOrchestrator()
        resume_result = orchestrator.extract_from_text(resume_text, "resume_input")

        if not resume_result.success:
            raise HTTPException(
                status_code=400,
                detail=f"Resume extraction failed: {resume_result.error}",
            )

        # Extract JD data
        jd_processed = process_text(job_description_text)
        jd_data = await extract_jd_data(jd_processed.cleaned_text)

        # Calculate ATS score
        ats_analyzer = get_ats_analyzer()
        ats_result = ats_analyzer.calculate_ats_score(
            resume_result.extracted_fields,
            jd_data,
        )

        logger.success(f"Quick ATS score: {ats_result.ats_score}/100")

        return ats_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick ATS score failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/full-analysis",
    response_model=FullCandidateAnalysis,
    summary="Full candidate analysis with fit scoring and red flags",
    description="""
    Comprehensive candidate analysis including:
    - ATS compatibility score (0-100)
    - Fit score with detailed breakdown (technical, experience, cultural, growth)
    - Red flag detection (employment gaps, short tenures, etc.)
    - Strengths and weaknesses analysis
    - Career progression assessment
    - Actionable recommendations

    Provide the job description as:
    - Text in the `job_description_text` field
    - A PDF file in the `job_description_file` field
    """,
)
async def full_candidate_analysis(
    resume_file: Annotated[UploadFile, File(description="Resume PDF file")],
    job_description_text: Annotated[
        str | None, Form(description="Job description as plain text")
    ] = None,
    job_description_file: Annotated[
        UploadFile | None, File(description="Job description as PDF file")
    ] = None,
) -> FullCandidateAnalysis:
    """
    Perform comprehensive candidate analysis.

    Combines ATS scoring with fit analysis, red flag detection,
    and actionable recommendations for hiring decisions.
    """
    start_time = time.time()

    # Validate inputs
    if not job_description_text and not job_description_file:
        raise HTTPException(
            status_code=400,
            detail="Either job_description_text or job_description_file is required",
        )

    if not resume_file.filename or not resume_file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Resume must be a PDF file",
        )

    temp_resume_path: Path | None = None
    temp_jd_path: Path | None = None

    try:
        # Save resume to temp file
        resume_content = await resume_file.read()
        temp_resume_path = save_temp_file(resume_content, resume_file.filename)

        # Extract resume data
        logger.processing(f"full candidate analysis: {resume_file.filename}")
        orchestrator = ExtractionOrchestrator()
        resume_result = orchestrator.extract_from_pdf(temp_resume_path)

        if not resume_result.success:
            return FullCandidateAnalysis(
                success=False,
                error=f"Resume extraction failed: {resume_result.error}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )

        resume_data = resume_result.extracted_fields

        # Get JD text
        if job_description_file and job_description_file.filename:
            jd_content = await job_description_file.read()
            temp_jd_path = save_temp_file(jd_content, job_description_file.filename)

            if job_description_file.filename.lower().endswith(".pdf"):
                jd_pdf_result = extract_text_from_pdf(temp_jd_path)
                jd_text = jd_pdf_result.text
            else:
                jd_text = jd_content.decode("utf-8", errors="ignore")
        else:
            jd_text = job_description_text or ""

        # Process JD text
        jd_processed = process_text(jd_text)

        # Extract JD data using LLM
        jd_data = await extract_jd_data(jd_processed.cleaned_text)

        # Calculate ATS score
        ats_analyzer = get_ats_analyzer()
        ats_result = ats_analyzer.calculate_ats_score(resume_data, jd_data)

        # Perform comprehensive candidate analysis (synchronous)
        candidate_analyzer = get_candidate_analyzer()
        fit_result = candidate_analyzer.analyze_candidate(resume_data, jd_data)

        processing_time = (time.time() - start_time) * 1000

        # Calculate overall score (weighted: 40% ATS + 60% Fit)
        overall_score = int(ats_result.ats_score * 0.4 + fit_result.fit_score * 0.6)

        logger.success(
            f"Full analysis complete: ATS={ats_result.ats_score}/100, "
            f"Fit={fit_result.fit_score}/100, Overall={overall_score}/100 "
            f"({processing_time:.0f}ms)"
        )

        return FullCandidateAnalysis(
            success=True,
            candidate_name=resume_data.get("candidate_name"),
            candidate_email=resume_data.get("email"),
            candidate_current_role=resume_data.get("current_role"),
            candidate_experience_years=resume_data.get("total_experience_years"),
            job_title=jd_data.get("job_title"),
            company_name=jd_data.get("company_name"),
            overall_score=overall_score,
            ats_score=ats_result.ats_score,
            matched_skills=ats_result.matched_skills,
            missing_skills=ats_result.missing_required_skills,
            fit_analysis=fit_result,
            resume_data=resume_data,
            jd_data=jd_data,
            processing_time_ms=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Full candidate analysis failed: {e}")
        import traceback

        traceback.print_exc()
        return FullCandidateAnalysis(
            success=False,
            error=str(e),
            processing_time_ms=(time.time() - start_time) * 1000,
        )
    finally:
        # Cleanup temp files
        if temp_resume_path:
            cleanup_temp_file(temp_resume_path)
        if temp_jd_path:
            cleanup_temp_file(temp_jd_path)


async def analyze_single_resume(
    resume_content: bytes,
    filename: str,
    jd_text: str,
    jd_data: dict[str, Any],
) -> FullCandidateAnalysis:
    """
    Analyze a single resume file asynchronously.

    Helper function for batch processing.
    """
    start_time = time.time()
    temp_resume_path: Path | None = None

    try:
        # Save resume to temp file
        temp_resume_path = save_temp_file(resume_content, filename)

        # Extract resume data
        orchestrator = ExtractionOrchestrator()
        resume_result = orchestrator.extract_from_pdf(temp_resume_path)

        if not resume_result.success:
            return FullCandidateAnalysis(
                success=False,
                error=f"Resume extraction failed: {resume_result.error}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )

        resume_data = resume_result.extracted_fields

        # Calculate ATS score
        ats_analyzer = get_ats_analyzer()
        ats_result = ats_analyzer.calculate_ats_score(resume_data, jd_data)

        # Perform fit analysis
        candidate_analyzer = get_candidate_analyzer()
        fit_result = candidate_analyzer.analyze_candidate(resume_data, jd_data)

        processing_time = (time.time() - start_time) * 1000

        # Calculate overall score (weighted: 40% ATS + 60% Fit)
        overall_score = int(ats_result.ats_score * 0.4 + fit_result.fit_score * 0.6)

        return FullCandidateAnalysis(
            success=True,
            candidate_name=resume_data.get("candidate_name"),
            candidate_email=resume_data.get("email"),
            candidate_current_role=resume_data.get("current_role"),
            candidate_experience_years=resume_data.get("total_experience_years"),
            job_title=jd_data.get("job_title"),
            company_name=jd_data.get("company_name"),
            overall_score=overall_score,
            ats_score=ats_result.ats_score,
            matched_skills=ats_result.matched_skills,
            missing_skills=ats_result.missing_required_skills,
            fit_analysis=fit_result,
            resume_data=resume_data,
            jd_data=jd_data,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"Resume analysis failed for {filename}: {e}")
        return FullCandidateAnalysis(
            success=False,
            error=str(e),
            processing_time_ms=(time.time() - start_time) * 1000,
        )
    finally:
        if temp_resume_path:
            cleanup_temp_file(temp_resume_path)


@router.post(
    "/rank",
    response_model=RankingResult,
    summary="Rank multiple resumes against a job description",
    description="""
    Upload multiple resumes and a job description to:
    - Rank all candidates by overall fit score
    - Get side-by-side comparison data
    - See score distribution and hiring recommendations
    - Identify the best candidate

    Supports up to 10 resumes at once for efficient batch processing.
    """,
)
async def rank_candidates(
    resume_files: Annotated[
        list[UploadFile], File(description="Resume PDF files (max 10)")
    ],
    job_description_text: Annotated[
        str | None, Form(description="Job description as plain text")
    ] = None,
    job_description_file: Annotated[
        UploadFile | None, File(description="Job description as PDF file")
    ] = None,
    job_title: Annotated[
        str | None,
        Form(description="Job title (optional, will extract from JD if not provided)"),
    ] = None,
    company_name: Annotated[
        str | None, Form(description="Company name (optional)")
    ] = None,
) -> RankingResult:
    """
    Rank multiple candidates against a job description.

    Returns ranked list with comparison data and hiring recommendations.
    """
    start_time = time.time()

    # Validate inputs
    if not job_description_text and not job_description_file:
        raise HTTPException(
            status_code=400,
            detail="Either job_description_text or job_description_file is required",
        )

    if not resume_files or len(resume_files) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one resume file is required",
        )

    if len(resume_files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 resume files allowed per request",
        )

    # Validate all files are PDFs
    for file in resume_files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"All files must be PDFs. Invalid file: {file.filename}",
            )

    temp_jd_path: Path | None = None

    try:
        logger.processing(f"Ranking {len(resume_files)} candidates")

        # Get JD text
        if job_description_file and job_description_file.filename:
            jd_content = await job_description_file.read()
            temp_jd_path = save_temp_file(jd_content, job_description_file.filename)

            if job_description_file.filename.lower().endswith(".pdf"):
                jd_pdf_result = extract_text_from_pdf(temp_jd_path)
                jd_text = jd_pdf_result.text
            else:
                jd_text = jd_content.decode("utf-8", errors="ignore")
        else:
            jd_text = job_description_text or ""

        # Process JD text
        jd_processed = process_text(jd_text)

        # Extract JD data using LLM
        jd_data = await extract_jd_data(jd_processed.cleaned_text)

        # Use provided job title/company or extract from JD
        final_job_title = job_title or jd_data.get("job_title")
        final_company_name = company_name or jd_data.get("company_name")

        # Read all resume contents upfront
        resume_contents: list[tuple[str, bytes]] = []
        for file in resume_files:
            content = await file.read()
            resume_contents.append((file.filename or "unknown.pdf", content))

        # Process all resumes concurrently using asyncio.gather
        # This significantly speeds up processing for multiple files
        logger.processing(
            f"Starting concurrent analysis of {len(resume_contents)} resumes"
        )

        async def analyze_with_filename(
            filename: str, content: bytes
        ) -> tuple[str, FullCandidateAnalysis]:
            """Wrapper to return filename with analysis result."""
            logger.processing(f"Analyzing resume: {filename}")
            analysis = await analyze_single_resume(
                resume_content=content,
                filename=filename,
                jd_text=jd_text,
                jd_data=jd_data,
            )
            return (filename, analysis)

        # Run all analyses concurrently
        tasks = [
            analyze_with_filename(filename, content)
            for filename, content in resume_contents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        analyses: dict[str, FullCandidateAnalysis] = {}
        for result_item in results:
            if isinstance(result_item, Exception):
                logger.error(f"Analysis failed: {result_item}")
                continue
            filename, analysis = result_item
            analyses[filename] = analysis

        # Rank candidates
        ranker = get_candidate_ranker()
        result = ranker.rank_candidates(
            analyses=analyses,
            job_title=final_job_title,
            company_name=final_company_name,
        )

        result.processing_time_ms = (time.time() - start_time) * 1000

        logger.success(
            f"Ranked {len(resume_files)} candidates in {result.processing_time_ms:.0f}ms. "
            f"Top candidate: {result.top_candidate.candidate_name if result.top_candidate else 'N/A'}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ranking failed: {e}")
        import traceback

        traceback.print_exc()
        return RankingResult(
            success=False,
            total_candidates=0,
            rankings=[],
            hiring_recommendation="Error during ranking",
            error=str(e),
            processing_time_ms=(time.time() - start_time) * 1000,
        )
    finally:
        if temp_jd_path:
            cleanup_temp_file(temp_jd_path)


@router.post(
    "/compare",
    response_model=CandidateComparison,
    summary="Compare two candidates side-by-side",
    description="""
    Upload two resumes and a job description for detailed side-by-side comparison:
    - Score differences
    - Unique skills of each candidate
    - Red flag comparison
    - Winner determination with reasons
    """,
)
async def compare_candidates(
    resume_file_1: Annotated[UploadFile, File(description="First resume PDF file")],
    resume_file_2: Annotated[UploadFile, File(description="Second resume PDF file")],
    job_description_text: Annotated[
        str | None, Form(description="Job description as plain text")
    ] = None,
    job_description_file: Annotated[
        UploadFile | None, File(description="Job description as PDF file")
    ] = None,
) -> CandidateComparison:
    """
    Compare two candidates side-by-side.

    Returns detailed comparison with winner determination.
    """
    # Validate inputs
    if not job_description_text and not job_description_file:
        raise HTTPException(
            status_code=400,
            detail="Either job_description_text or job_description_file is required",
        )

    for file, name in [(resume_file_1, "Resume 1"), (resume_file_2, "Resume 2")]:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"{name} must be a PDF file",
            )

    temp_jd_path: Path | None = None

    try:
        logger.processing("Comparing two candidates")

        # Get JD text
        if job_description_file and job_description_file.filename:
            jd_content = await job_description_file.read()
            temp_jd_path = save_temp_file(jd_content, job_description_file.filename)

            if job_description_file.filename.lower().endswith(".pdf"):
                jd_pdf_result = extract_text_from_pdf(temp_jd_path)
                jd_text = jd_pdf_result.text
            else:
                jd_text = jd_content.decode("utf-8", errors="ignore")
        else:
            jd_text = job_description_text or ""

        # Process JD text
        jd_processed = process_text(jd_text)

        # Extract JD data using LLM
        jd_data = await extract_jd_data(jd_processed.cleaned_text)

        # Read resume contents
        content_1 = await resume_file_1.read()
        content_2 = await resume_file_2.read()

        # Analyze both resumes
        analysis_1 = await analyze_single_resume(
            resume_content=content_1,
            filename=resume_file_1.filename or "resume1.pdf",
            jd_text=jd_text,
            jd_data=jd_data,
        )

        analysis_2 = await analyze_single_resume(
            resume_content=content_2,
            filename=resume_file_2.filename or "resume2.pdf",
            jd_text=jd_text,
            jd_data=jd_data,
        )

        # Compare candidates
        ranker = get_candidate_ranker()
        comparison = ranker.compare_candidates(
            analysis_1=analysis_1,
            analysis_2=analysis_2,
            file_name_1=resume_file_1.filename or "resume1.pdf",
            file_name_2=resume_file_2.filename or "resume2.pdf",
        )

        logger.success(
            f"Comparison complete. Winner: Candidate {comparison.winner} "
            f"({comparison.overall_score_1} vs {comparison.overall_score_2})"
        )

        return comparison

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_jd_path:
            cleanup_temp_file(temp_jd_path)
