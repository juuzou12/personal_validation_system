import logging
from typing import Dict, Any, Optional, Tuple
import os
import tempfile

from ..models.validation_models import (
    ValidationRequest, 
    ValidationResponse, 
    FaceMatchResult,
    IDValidationResult,
    OCRResult
)
from ..utils.image_utils import (
    load_image, 
    detect_faces, 
    compare_faces,
    save_uploaded_file,
    cleanup_temp_file,
    ImageProcessingError
)
from ..utils.ocr_utils import OCRService

logger = logging.getLogger(__name__)

class ValidationService:
    """Service for validating Kenyan ID information"""
    
    def __init__(self, use_gpu: bool = False):
        """
        Initialize the validation service
        
        Args:
            use_gpu: Whether to use GPU for processing (if available)
        """
        self.ocr_service = OCRService(use_gpu=use_gpu)
    
    async def validate_kenyan_id(self, request: ValidationRequest, 
                               selfie_file, id_front_file, id_back_file) -> ValidationResponse:
        """
        Validate Kenyan ID with selfie and ID card images
        
        Args:
            request: Validation request data
            selfie_file: Uploaded selfie image
            id_front_file: Front side of ID card
            id_back_file: Back side of ID card
            
        Returns:
            ValidationResponse with validation results
        """
        temp_files = []
        try:
            # Save uploaded files to temporary location
            selfie_path = save_uploaded_file(selfie_file, "_selfie.jpg")
            id_front_path = save_uploaded_file(id_front_file, "_id_front.jpg")
            id_back_path = save_uploaded_file(id_back_file, "_id_back.jpg")
            temp_files.extend([selfie_path, id_front_path, id_back_path])
            
            # Step 1: Validate ID number format
            id_validation = self._validate_id_number(request.id_number)
            
            # Step 2: Extract text from ID card using OCR
            ocr_result = await self._process_id_card(id_front_path, id_back_path)
            
            # Step 3: Compare selfie with ID photo
            face_match_result = await self._compare_faces(selfie_path, id_front_path)
            
            # Step 4: Validate phone number
            phone_validation = self._validate_phone_number(request.phone_number)
            
            # Step 5: Verify name matches between request and ID card
            name_match = self._verify_name_match(request.name, ocr_result.full_name)
            
            # Determine overall validation result
            is_verified = all([
                id_validation.id_number_valid,
                id_validation.id_pattern_matched,
                face_match_result.is_match,
                phone_validation['is_valid'],
                name_match
            ])
            
            return ValidationResponse(
                status="success",
                message="Validation completed successfully",
                is_verified=is_verified,
                validation_details={
                    "id_validation": id_validation.dict(),
                    "face_match": face_match_result.dict(),
                    "phone_validation": phone_validation,
                    "name_match": name_match,
                    "ocr_extracted_data": ocr_result.dict()
                }
            )
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}", exc_info=True)
            return ValidationResponse(
                status="error",
                message=f"Validation failed: {str(e)}",
                is_verified=False
            )
            
        finally:
            # Clean up temporary files
            for file_path in temp_files:
                cleanup_temp_file(file_path)
    
    def _validate_id_number(self, id_number: str) -> IDValidationResult:
        """Validate Kenyan ID number format and checksum"""
        is_valid = self.ocr_service.validate_kenyan_id_number(id_number)
        
        # For Kenyan IDs, we can add more specific validation here
        # For now, we're just checking the basic format
        return IDValidationResult(
            id_number_valid=is_valid,
            id_pattern_matched=is_valid,
            extracted_data=OCRResult()
        )
    
    async def _process_id_card(self, front_path: str, back_path: str) -> OCRResult:
        """Process ID card images and extract information"""
        # Process front of ID (usually has photo and basic info)
        front_details = self.ocr_service.extract_kenyan_id_details(front_path)
        
        # Process back of ID (may have additional info)
        back_details = self.ocr_service.extract_kenyan_id_details(back_path)
        
        # Merge results (prioritize front details)
        merged_details = {**back_details, **front_details}
        
        return OCRResult(
            id_number=merged_details.get('id_number'),
            full_name=merged_details.get('full_name'),
            date_of_birth=merged_details.get('date_of_birth'),
            gender=merged_details.get('gender'),
            other_details={
                k: v for k, v in merged_details.items()
                if k not in ['id_number', 'full_name', 'date_of_birth', 'gender']
            }
        )
    
    async def _compare_faces(self, selfie_path: str, id_photo_path: str) -> FaceMatchResult:
        """Compare face in selfie with face in ID photo"""
        try:
            # Load images
            selfie_img = load_image(selfie_path)
            id_photo_img = load_image(id_photo_path)
            
            # Detect faces
            selfie_has_face, _ = detect_faces(selfie_img)
            id_has_face, _ = detect_faces(id_photo_img)
            
            if not selfie_has_face or not id_has_face:
                return FaceMatchResult(
                    is_match=False,
                    confidence=0.0,
                    message="Could not detect faces in one or both images"
                )
            
            # Compare faces
            result = compare_faces(selfie_img, id_photo_img)
            
            return FaceMatchResult(
                is_match=result['is_match'],
                confidence=result['confidence'],
                message=result['message']
            )
            
        except Exception as e:
            logger.error(f"Face comparison error: {str(e)}", exc_info=True)
            return FaceMatchResult(
                is_match=False,
                confidence=0.0,
                message=f"Error comparing faces: {str(e)}"
            )
    
    def _validate_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """Validate phone number format"""
        try:
            # Basic validation for Kenyan numbers
            if not phone_number.startswith('+254'):
                return {
                    'is_valid': False,
                    'message': 'Phone number must start with +254',
                    'normalized_number': None
                }
                
            # Check if it's a valid Kenyan mobile number
            if not phone_number[4:].isdigit() or len(phone_number) != 13:
                return {
                    'is_valid': False,
                    'message': 'Invalid phone number format',
                    'normalized_number': None
                }
                
            return {
                'is_valid': True,
                'message': 'Valid phone number',
                'normalized_number': phone_number
            }
            
        except Exception as e:
            logger.error(f"Phone validation error: {str(e)}")
            return {
                'is_valid': False,
                'message': f'Error validating phone number: {str(e)}',
                'normalized_number': None
            }
    
    def _verify_name_match(self, provided_name: str, extracted_name: Optional[str]) -> bool:
        """Verify if the provided name matches the extracted name"""
        if not extracted_name:
            return False
            
        # Simple case-insensitive comparison
        # In a real application, you might want to use more sophisticated matching
        # to handle minor differences in formatting, middle names, etc.
        return provided_name.lower() == extracted_name.lower()
