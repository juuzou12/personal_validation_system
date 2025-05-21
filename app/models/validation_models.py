from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum

class IDType(str, Enum):
    KENYAN = "kenyan"
    OTHER = "other"

class ValidationRequest(BaseModel):
    name: str = Field(..., description="Full name as per ID")
    id_number: str = Field(..., description="National ID number")
    phone_number: str = Field(..., description="Phone number with country code")
    id_type: IDType = Field(default=IDType.KENYAN, description="Type of ID document")

    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Basic validation for Kenyan phone numbers
        if not v.startswith('+254'):
            raise ValueError('Phone number must start with +254')
        if not v[1:].isdigit() or len(v) != 13:
            raise ValueError('Invalid phone number format')
        return v

class ValidationResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None
    validation_details: Optional[dict] = None
    is_verified: bool = False

class OCRResult(BaseModel):
    id_number: Optional[str] = None
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    other_details: dict = {}

class FaceMatchResult(BaseModel):
    is_match: bool
    confidence: float
    message: str

class IDValidationResult(BaseModel):
    id_number_valid: bool
    id_pattern_matched: bool
    extracted_data: Optional[OCRResult] = None
    face_match: Optional[FaceMatchResult] = None
    phone_validation: Optional[dict] = None
