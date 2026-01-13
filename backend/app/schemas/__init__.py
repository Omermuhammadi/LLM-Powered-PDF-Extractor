"""
Pydantic schemas module.

This module exports all schema classes for use throughout the application.
"""

from app.schemas.ats import (
    ATSScoreResult,
    JobDescriptionData,
    ResumeJDAnalysisRequest,
    ResumeJDAnalysisResult,
    SkillMatch,
)
from app.schemas.base import (
    BaseExtractedData,
    FieldConfidence,
    FieldScore,
    ValidationResult,
    ValidationSeverity,
    validate_extracted_data,
)
from app.schemas.candidate import (
    CandidateFitResult,
    CareerProgression,
    FitScoreBreakdown,
    FullCandidateAnalysis,
    RecommendationType,
    RedFlag,
    RedFlagSeverity,
    RedFlagType,
    StrengthItem,
)
from app.schemas.extraction import (
    BatchExtractionRequest,
    BatchExtractionResponse,
    DocumentMetadata,
    DocumentType,
    ExtractionError,
    ExtractionMetrics,
    ExtractionResponse,
    ExtractionStatus,
    PageInfo,
    ProcessingStage,
    ValidationSummary,
)
from app.schemas.invoice import (
    CustomerInfo,
    Invoice,
    InvoiceData,
    LineItem,
    PaymentInfo,
    VendorInfo,
)
from app.schemas.resume import (
    CertificationItem,
    EducationItem,
    ExperienceItem,
    ProjectItem,
    Resume,
    ResumeData,
)

__all__ = [
    # Base schemas
    "BaseExtractedData",
    "FieldConfidence",
    "FieldScore",
    "ValidationResult",
    "ValidationSeverity",
    "validate_extracted_data",
    # Extraction schemas
    "BatchExtractionRequest",
    "BatchExtractionResponse",
    "DocumentMetadata",
    "DocumentType",
    "ExtractionError",
    "ExtractionMetrics",
    "ExtractionResponse",
    "ExtractionStatus",
    "PageInfo",
    "ProcessingStage",
    "ValidationSummary",
    # Invoice schemas
    "CustomerInfo",
    "Invoice",
    "InvoiceData",
    "LineItem",
    "PaymentInfo",
    "VendorInfo",
    # Resume schemas
    "CertificationItem",
    "EducationItem",
    "ExperienceItem",
    "ProjectItem",
    "Resume",
    "ResumeData",
    # ATS schemas
    "ATSScoreResult",
    "JobDescriptionData",
    "ResumeJDAnalysisRequest",
    "ResumeJDAnalysisResult",
    "SkillMatch",
    # Candidate fit schemas
    "CareerProgression",
    "CandidateFitResult",
    "FitScoreBreakdown",
    "FullCandidateAnalysis",
    "RecommendationType",
    "RedFlag",
    "RedFlagSeverity",
    "RedFlagType",
    "StrengthItem",
]
