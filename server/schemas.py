from pydantic import BaseModel, Field, ConfigDict, field_validator

MEDICAL_DISCLAIMER = "This is not medical advice. Consult a healthcare professional."

class QuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(..., min_length=1, max_length=1000)

    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Question cannot be empty')
        return v


class QuestionResponse(BaseModel):
    response: str
    sources: list[str]
    disclaimer: str = MEDICAL_DISCLAIMER


class UploadFileSchema(BaseModel):
    filename: str
    content_type: str
    size: int

    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v):
        if v != "application/pdf":
            raise ValueError(f"Only PDF files are allowed")
        return v

    @field_validator('size')
    @classmethod
    def validate_size(cls, v):
        max_size = 10 * 1024 * 1024  # ~ 10MB
        if v > max_size:
            raise ValueError(f"File size exceeds {max_size} bytes")
        return v
