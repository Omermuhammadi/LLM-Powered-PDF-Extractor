"""
Resume/CV Pydantic schemas with comprehensive field extraction.

This module defines the data models for resume extraction results,
including personal info, experience, education, skills, and confidence scoring.
Designed for production-grade HR/recruitment intelligence.
"""

import re
from typing import Optional

from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseExtractedData, FieldConfidence


class ExperienceItem(BaseExtractedData):
    """Model for work experience entries."""

    company: Optional[str] = Field(
        default=None,
        description="Company or organization name",
    )
    role: Optional[str] = Field(
        default=None,
        description="Job title or position",
    )
    duration: Optional[str] = Field(
        default=None,
        description="Duration string (e.g., 'Jan 2022 - Present')",
    )
    duration_months: Optional[int] = Field(
        default=None,
        ge=0,
        description="Duration in months (calculated from dates)",
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date in YYYY-MM format",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM format or 'Present'",
    )
    location: Optional[str] = Field(
        default=None,
        description="Job location (city, country)",
    )
    highlights: list[str] = Field(
        default_factory=list,
        description="Key achievements and responsibilities",
    )
    is_current: bool = Field(
        default=False,
        description="Whether this is the current position",
    )

    # Confidence scores
    company_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for company field",
    )
    role_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for role field",
    )


class EducationItem(BaseExtractedData):
    """Model for education entries."""

    institution: Optional[str] = Field(
        default=None,
        description="School, university, or institution name",
    )
    degree: Optional[str] = Field(
        default=None,
        description="Degree type (e.g., 'Bachelor of Science', 'MBA')",
    )
    field_of_study: Optional[str] = Field(
        default=None,
        description="Major or field of study",
    )
    year: Optional[str] = Field(
        default=None,
        description="Graduation year or year range",
    )
    start_year: Optional[int] = Field(
        default=None,
        ge=1950,
        le=2100,
        description="Start year",
    )
    end_year: Optional[int] = Field(
        default=None,
        ge=1950,
        le=2100,
        description="End/graduation year",
    )
    gpa: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=5.0,
        description="GPA if mentioned (normalized to 4.0 scale)",
    )
    honors: Optional[str] = Field(
        default=None,
        description="Honors, distinctions (e.g., 'Magna Cum Laude')",
    )
    location: Optional[str] = Field(
        default=None,
        description="Institution location",
    )

    # Confidence scores
    institution_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for institution field",
    )
    degree_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for degree field",
    )


class CertificationItem(BaseExtractedData):
    """Model for certifications and licenses."""

    name: Optional[str] = Field(
        default=None,
        description="Certification name",
    )
    issuer: Optional[str] = Field(
        default=None,
        description="Issuing organization",
    )
    date_obtained: Optional[str] = Field(
        default=None,
        description="Date obtained",
    )
    expiry_date: Optional[str] = Field(
        default=None,
        description="Expiration date if applicable",
    )
    credential_id: Optional[str] = Field(
        default=None,
        description="Credential ID or license number",
    )


class ProjectItem(BaseExtractedData):
    """Model for project entries."""

    name: Optional[str] = Field(
        default=None,
        description="Project name",
    )
    description: Optional[str] = Field(
        default=None,
        description="Project description",
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies used",
    )
    url: Optional[str] = Field(
        default=None,
        description="Project URL if available",
    )
    duration: Optional[str] = Field(
        default=None,
        description="Project duration",
    )


class ResumeData(BaseExtractedData):
    """
    Complete resume data model with all extracted fields.

    This is the main schema for resume extraction results,
    containing all relevant candidate information with confidence scores.
    Designed for HR/recruitment intelligence and ATS compatibility.
    """

    # =========================================================================
    # Personal Information
    # =========================================================================
    candidate_name: Optional[str] = Field(
        default=None,
        description="Full name of the candidate",
    )
    email: Optional[str] = Field(
        default=None,
        description="Email address",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Phone number",
    )
    location: Optional[str] = Field(
        default=None,
        description="Location (City, State/Country)",
    )
    linkedin_url: Optional[str] = Field(
        default=None,
        description="LinkedIn profile URL",
    )
    github_url: Optional[str] = Field(
        default=None,
        description="GitHub profile URL",
    )
    portfolio_url: Optional[str] = Field(
        default=None,
        description="Portfolio or personal website URL",
    )

    # =========================================================================
    # Current Position
    # =========================================================================
    current_role: Optional[str] = Field(
        default=None,
        description="Current or most recent job title",
    )
    current_company: Optional[str] = Field(
        default=None,
        description="Current or most recent employer",
    )

    # =========================================================================
    # Professional Summary
    # =========================================================================
    summary: Optional[str] = Field(
        default=None,
        description="Professional summary or objective statement",
    )
    total_experience_years: Optional[float] = Field(
        default=None,
        ge=0,
        description="Total years of professional experience",
    )

    # =========================================================================
    # Skills
    # =========================================================================
    skills: list[str] = Field(
        default_factory=list,
        description="List of all skills mentioned",
    )
    technical_skills: list[str] = Field(
        default_factory=list,
        description="Technical/hard skills",
    )
    soft_skills: list[str] = Field(
        default_factory=list,
        description="Soft/interpersonal skills",
    )

    # =========================================================================
    # Experience
    # =========================================================================
    experience: list[ExperienceItem] = Field(
        default_factory=list,
        description="Work experience entries (most recent first)",
    )

    # =========================================================================
    # Education
    # =========================================================================
    education: list[EducationItem] = Field(
        default_factory=list,
        description="Education entries",
    )

    # =========================================================================
    # Certifications & Projects
    # =========================================================================
    certifications: list[str] = Field(
        default_factory=list,
        description="List of certifications (simple string format)",
    )
    certifications_detailed: list[CertificationItem] = Field(
        default_factory=list,
        description="Detailed certification entries",
    )
    projects: list[ProjectItem] = Field(
        default_factory=list,
        description="Notable projects",
    )

    # =========================================================================
    # Languages
    # =========================================================================
    languages: list[str] = Field(
        default_factory=list,
        description="Languages with proficiency (e.g., 'English: Fluent')",
    )

    # =========================================================================
    # Additional Fields
    # =========================================================================
    awards: list[str] = Field(
        default_factory=list,
        description="Awards and honors",
    )
    publications: list[str] = Field(
        default_factory=list,
        description="Publications if any",
    )
    interests: list[str] = Field(
        default_factory=list,
        description="Hobbies and interests",
    )
    references: Optional[str] = Field(
        default=None,
        description="References section content",
    )

    # =========================================================================
    # Confidence Scores for Key Fields
    # =========================================================================
    candidate_name_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for candidate_name",
    )
    email_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for email",
    )
    phone_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for phone",
    )
    experience_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for experience section",
    )
    education_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for education section",
    )
    skills_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for skills section",
    )

    # =========================================================================
    # Validators
    # =========================================================================
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize email."""
        if v is None:
            return None
        v = v.strip().lower()
        # Basic email pattern check
        if v and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            return None  # Invalid email, set to None
        return v

    @field_validator("linkedin_url", "github_url", "portfolio_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Clean and validate URLs."""
        if v is None:
            return None
        v = v.strip()
        # Add https if missing
        if v and not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v

    @field_validator("skills", "technical_skills", "soft_skills", mode="before")
    @classmethod
    def ensure_list(cls, v):
        """Ensure skills are always a list."""
        if v is None:
            return []
        if isinstance(v, str):
            # Split by common delimiters
            return [s.strip() for s in re.split(r"[,;|]", v) if s.strip()]
        return v

    @model_validator(mode="after")
    def infer_current_position(self) -> "ResumeData":
        """Infer current role/company from experience if not set."""
        try:
            if self.experience and len(self.experience) > 0:
                # Get the most recent (first) experience
                latest = self.experience[0]
                if not self.current_role and latest.role:
                    self.current_role = latest.role
                if not self.current_company and latest.company:
                    self.current_company = latest.company
        except (IndexError, AttributeError):
            pass
        return self

    @model_validator(mode="after")
    def calculate_total_experience(self) -> "ResumeData":
        """Calculate total experience from individual positions."""
        try:
            if self.total_experience_years is None and self.experience:
                total_months = 0
                for exp in self.experience:
                    if exp.duration_months:
                        total_months += exp.duration_months
                if total_months > 0:
                    self.total_experience_years = round(total_months / 12, 1)
        except Exception:
            pass
        return self

    def get_field_summary(self) -> dict[str, bool]:
        """Get summary of which fields were extracted."""
        return {
            "candidate_name": self.candidate_name is not None,
            "email": self.email is not None,
            "phone": self.phone is not None,
            "location": self.location is not None,
            "linkedin": self.linkedin_url is not None,
            "summary": self.summary is not None,
            "skills": len(self.skills) > 0,
            "experience": len(self.experience) > 0,
            "education": len(self.education) > 0,
            "certifications": len(self.certifications) > 0,
        }

    def get_skills_count(self) -> int:
        """Get total number of unique skills."""
        all_skills = set(self.skills + self.technical_skills + self.soft_skills)
        return len(all_skills)

    def get_experience_count(self) -> int:
        """Get number of experience entries."""
        return len(self.experience)

    def get_education_count(self) -> int:
        """Get number of education entries."""
        return len(self.education)


# Type alias for backward compatibility
Resume = ResumeData
