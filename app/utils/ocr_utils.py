import logging
import re
from typing import Dict, Optional, Tuple
import pytesseract
import easyocr
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

class OCRService:
    """Service for performing OCR on ID card images"""
    
    def __init__(self, use_gpu: bool = False):
        """
        Initialize OCR service
        
        Args:
            use_gpu: Whether to use GPU for OCR (requires CUDA)
        """
        self.use_easyocr = True  # Default to EasyOCR for better accuracy
        self.reader = easyocr.Reader(['en'], gpu=use_gpu) if self.use_easyocr else None
        
        # Kenyan ID specific patterns
        self.kenyan_id_pattern = re.compile(r'^\d{8,9}$')  # Kenyan ID numbers are 8-9 digits
        self.phone_pattern = re.compile(r'(?:\+?254|0)?[17]\d{8}$')  # Kenyan phone number pattern
    
    def extract_text(self, image_path: str) -> Tuple[bool, str]:
        """
        Extract text from an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            tuple: (success, text) - success flag and extracted text
        """
        try:
            if self.use_easyocr:
                result = self.reader.readtext(image_path, detail=0)
                text = '\n'.join(result)
            else:
                image = Image.open(image_path)
                text = pytesseract.image_to_string(image)
                
            return True, text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return False, str(e)
    
    def extract_kenyan_id_details(self, image_path: str) -> Dict[str, str]:
        """
        Extract structured data from a Kenyan ID card image
        
        Args:
            image_path: Path to the ID card image
            
        Returns:
            dict: Extracted ID details
        """
        result = {
            'id_number': None,
            'full_name': None,
            'date_of_birth': None,
            'gender': None,
            'other_details': {}
        }
        
        success, text = self.extract_text(image_path)
        if not success:
            return result
            
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Try to find ID number (8-9 digits)
        for line in lines:
            # Look for ID number
            if not result['id_number'] and self.kenyan_id_pattern.fullmatch(line):
                result['id_number'] = line
                continue
                
            # Look for date of birth (various formats)
            if not result['date_of_birth']:
                # Look for dates like DD/MM/YYYY or DD-MM-YYYY
                date_match = re.search(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b', line)
                if date_match:
                    result['date_of_birth'] = date_match.group(1)
            
            # Look for gender
            if not result['gender']:
                gender_match = re.search(r'\b(?:SEX|GENDER)[:\s]*(\w+)\b', line, re.IGNORECASE)
                if gender_match:
                    result['gender'] = gender_match.group(1).capitalize()
            
            # Look for name (usually one of the first few lines)
            if not result['full_name'] and len(lines) > 0 and len(line.split()) >= 2:
                # Simple heuristic: if line looks like a name (has at least 2 words with uppercase first letters)
                if all(word[0].isupper() for word in line.split() if len(word) > 1):
                    result['full_name'] = line
        
        return result
    
    def validate_kenyan_id_number(self, id_number: str) -> bool:
        """
        Validate Kenyan ID number format
        
        Args:
            id_number: ID number to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not id_number:
            return False
            
        # Kenyan ID numbers are 8-9 digits
        return bool(self.kenyan_id_pattern.fullmatch(str(id_number)))
    
    def extract_phone_number(self, text: str) -> Optional[str]:
        """
        Extract phone number from text
        
        Args:
            text: Text to search for phone number
            
        Returns:
            str: Extracted phone number or None if not found
        """
        # Look for phone numbers in various formats
        phone_matches = self.phone_pattern.findall(text)
        if phone_matches:
            # Clean up the phone number
            phone = phone_matches[0]
            # Convert to E.164 format (+254...)
            if phone.startswith('0'):
                return '+254' + phone[1:]
            elif phone.startswith('254'):
                return '+' + phone
            elif not phone.startswith('+'):
                return '+254' + phone
            return phone
        return None
