import re
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, field_validator
from .constants.K import (
    MEDICAL_DISCLAIMER,
    MAX_QUESTION_LENGTH,
    MAX_ANSWER_LENGTH,
    MAX_SOURCE_LENGTH,
    MAX_UPLOAD_FILES,
    ALLOWED_FILE_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_SOURCES,
)


class QuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_LENGTH)

    @field_validator("question")
    @classmethod
    def validate_question(cls, v):
        # validate for null characters
        if "\x00" in v:
            raise ValueError("Question cannot contain null characters")

        v = v.strip()

        # validate for empty questions
        if not v:
            raise ValueError("Question cannot be empty")

        v = re.sub(r"\s+", " ", v)

        # validate for length after stripping and normalizing whitespace
        if len(v) > MAX_QUESTION_LENGTH:
            raise ValueError(
                f"Question exceeds maximum length of {MAX_QUESTION_LENGTH} characters"
            )
        return v


class QuestionResponse(BaseModel):
    response: str = Field(..., min_length=1, max_length=MAX_ANSWER_LENGTH)
    sources: list[str] = Field(default_factory=list, max_length=MAX_SOURCES)
    disclaimer: str = MEDICAL_DISCLAIMER
    injection_detected: bool = False
    pii_redacted: bool = False

    # reject unknown fields added by the user
    model_config = ConfigDict(extra="forbid")

    @field_validator("sources", mode="before")
    @classmethod
    def validate_sources(cls, v):
        if v is None:
            raise ValueError("Sources cannot be None")

        if not isinstance(v, list):
            raise ValueError("Sources must be a list")

        cleaned_sources = []
        seen = set()  # rejects duplicates and empty strings

        for source in v:
            if not isinstance(source, str):
                raise ValueError("Source must be strings")

            # accounts for strings with whitespace " " edge case when checking empty strings
            source = source.strip()

            if not source:
                raise ValueError("Source cannot contain empty strings")

            if len(source) > MAX_SOURCE_LENGTH:
                raise ValueError(
                    f"Source exceeds maximum length of {MAX_SOURCE_LENGTH} characters"
                )

            if source not in seen:
                seen.add(source)
                cleaned_sources.append(source)

        return cleaned_sources


class UploadFileSchema(BaseModel):
    filename: str
    content_type: str
    size: int

    # reject unknown fields added by the user
    model_config = ConfigDict(extra="forbid")

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v):
        if v != "application/pdf":
            raise ValueError(f"Only PDF files are allowed")
        return v

    @field_validator("size")
    @classmethod
    def validate_size(cls, v):
        max_size = 10 * 1024 * 1024  # ~ 10MB
        if v > max_size:
            raise ValueError(f"File size exceeds {max_size} bytes")
        return v

    @field_validator("filename")
    @classmethod
    def validate_filenam(cls, v):
        if not v:
            raise ValueError("Filename cannot be empty")

        if Path(v).suffix.lower() not in ALLOWED_FILE_EXTENSIONS:
            raise ValueError("Only PDF files are allowed.")

        return v


class UploadResponse(BaseModel):
    status: str
    uploaded_count: int
    rejected_count: int = 0
    files: list[UploadFileSchema]

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in {"success", "partial_success", "failed"}:
            raise ValueError("Invalid upload status")
        return v