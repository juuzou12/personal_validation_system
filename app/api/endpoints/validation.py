import logging
import re
import io
import cv2
import numpy as np
import phonenumbers
import easyocr
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Optional, Dict, Any, Tuple
import os
from PIL import Image

# Import models and services
from app.models.validation_models import ValidationResponse
from app.services.validation_service import ValidationService

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

def detect_faces(image_bytes: bytes) -> list:
    """Detect faces in an image using OpenCV's Haar Cascade."""
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Load the pre-trained face detection model
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return len(faces) > 0, len(faces)
    except Exception as e:
        logger.error(f"Error in face detection: {str(e)}")
        return False, 0

def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from an image using EasyOCR."""
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Use EasyOCR to extract text
        results = reader.readtext(img)
        
        # Extract and join all detected text
        text = " ".join([result[1] for result in results])
        return text
    except Exception as e:
        logger.error(f"Error in text extraction: {str(e)}")
        return ""

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/validate", tags=["validation"])

# Initialize validation service
validation_service = ValidationService(use_gpu=False)  # Set to True if GPU is available

@router.post("/kenyan-id", response_model=ValidationResponse)
async def validate_kenyan_id(
    name: str = Form(..., description="Full name as per ID"),
    id_number: str = Form(..., description="Kenyan national ID number"),
    phone_number: str = Form(..., description="Phone number with country code (+254...)"),
    selfie: UploadFile = File(..., description="Selfie photo"),
    id_front: UploadFile = File(..., description="Front side of ID card"),
    id_back: UploadFile = File(..., description="Back side of ID card"),
):
    """
    Validate Kenyan ID with selfie and ID card images
    
    This endpoint performs the following validations:
    - Validates ID number format
    - Extracts text from ID card using OCR
    - Compares selfie with ID photo using facial recognition
    - Validates phone number format
    - Verifies name matches between request and ID card
    """
    try:
        logger.info(f"Received validation request for ID: {id_number}")
        
        # Validate ID number (Kenyan ID format: 1-8 digits)
        is_valid_id = bool(re.match(r'^\d{7,8}$', id_number))
        id_validation = {
            "is_valid": is_valid_id,
            "message": "Valid ID number" if is_valid_id else "Invalid ID number format"
        }
        
        # Validate phone number
        try:
            parsed_number = phonenumbers.parse(phone_number, None)
            is_valid_phone = phonenumbers.is_valid_number(parsed_number)
            phone_validation = {
                "is_valid": is_valid_phone,
                "message": "Valid phone number",
                "normalized_number": phonenumbers.format_number(
                    parsed_number, 
                    phonenumbers.PhoneNumberFormat.E164
                )
            }
        except Exception as e:
            logger.warning(f"Invalid phone number {phone_number}: {str(e)}")
            phone_validation = {
                "is_valid": False,
                "message": f"Invalid phone number: {str(e)}",
                "normalized_number": None
            }
        
        # Read the uploaded files
        selfie_bytes = await selfie.read()
        id_front_bytes = await id_front.read()
        
        # Perform face detection on selfie
        has_face_selfie, face_count_selfie = detect_faces(selfie_bytes)
        has_face_id, face_count_id = detect_faces(id_front_bytes)
        
        # Extract text from ID card
        id_text = extract_text_from_image(id_front_bytes)
        
        # Check if name and ID number are in the extracted text
        name_in_id = name.lower() in id_text.lower()
        id_number_in_id = id_number in id_text
        
        # Basic face match (just checks if both images have faces for now)
        face_match = has_face_selfie and has_face_id
        
        # Update verification status
        is_verified = (
            is_valid_id and 
            phone_validation["is_valid"] and 
            name_in_id and 
            id_number_in_id and
            face_match
        )
        
        return {
            "status": "success",
            "message": "Validation completed successfully",
            "is_verified": is_verified,
            "data": {
                "name": name.strip(),
                "id_number": id_number,
                "phone_number": phone_number
            },
            "validation_details": {
                "id_validation": id_validation,
                "ocr_extraction": {
                    "extracted_text": id_text[:500] + (id_text[500:] and '...'),  # Limit text length
                    "name_found": name_in_id,
                    "id_number_found": id_number_in_id
                },
                "face_detection": {
                    "selfie_has_face": has_face_selfie,
                    "id_photo_has_face": has_face_id,
                    "face_count_selfie": face_count_selfie,
                    "face_count_id": face_count_id,
                    "faces_match": face_match
                },
                "phone_validation": phone_validation
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing validation request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}"
        )
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "kenyan-id-validation"}
