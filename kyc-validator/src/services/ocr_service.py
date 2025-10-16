import easyocr
import pytesseract
import numpy as np
from PIL import Image
import io
import re

reader = easyocr.Reader(['en'], gpu=False)  # Use CPU mode by default

def extract_text_easyocr(image_bytes: bytes):
    """
    Extract text using EasyOCR.
    """
    image_stream = io.BytesIO(image_bytes)
    image = Image.open(image_stream).convert('RGB')
    results = reader.readtext(np.array(image), detail=0)
    return " ".join(results)


def extract_text_tesseract(image_bytes: bytes):
    """
    Extract text using pytesseract.
    """
    image_stream = io.BytesIO(image_bytes)
    image = Image.open(image_stream)
    text = pytesseract.image_to_string(image)
    return text.strip()

def parse_id_info(ocr_text: str) -> dict:
    """
    Parse important information from ID card OCR text.
    
    Args:
        ocr_text: Raw text extracted from ID card image
        
    Returns:
        dict: Parsed ID information with standardized fields
    """
    # Initialize with default values
    id_info = {
        'id_number': None,
        'full_name': None,
        'date_of_birth': None,
        'gender': None,
        'document_type': None,
        'nationality': None,
        'place_of_issue': None,
        'date_of_issue': None,
        'expiry_date': None,
        'district_of_birth': None,
        'raw_text': ocr_text
    }
    
    try:
        # Convert to lowercase for case-insensitive matching
        text = ocr_text.lower()
        
        # Determine document type
        if 'huduma' in text:
            id_info['document_type'] = 'huduma_card'
        elif 'national' in text and 'identity' in text:
            id_info['document_type'] = 'national_id'
        
        # Extract ID Number
        if id_info['document_type'] == 'huduma_card':
            # Special handling for Huduma card ID format
            id_match = re.search(r'id\s*number[\s:]*([a-z0-9]+)', text, re.IGNORECASE)
            if not id_match:
                # Fallback if the format is slightly different
                id_match = re.search(r'id\s*number[^a-z0-9]*([a-z0-9]{5,})', text, re.IGNORECASE)
        else:  # national_id
            id_match = re.search(r'(?:id\s*(?:no\.?|number)?\s*[\s:]+|namba\s*ya\s*kitambulisho[\s:]+)([a-z0-9\s]+?)(?=\s+[a-z]+\s*[\s:]|$)', text, re.IGNORECASE)
        
        if id_match:
            id_info['id_number'] = id_match.group(1).strip().upper()
        
        # Extract Full Name
        if id_info['document_type'] == 'huduma_card':
            # Handle Huduma card name format
            name_match = re.search(r'(?:full\s*names?|jina\s*kamili)[\s:]*([a-z\s]+?)(?=date\s*of\s*birth|dob|sex|$)', text, re.IGNORECASE)
            if name_match:
                id_info['full_name'] = ' '.join([word.capitalize() for word in name_match.group(1).strip().split()])
        else:  # national_id
            # Try to get surname and given names
            surname = re.search(r'surname[\s:]+([a-z\s-]+?)(?=\s+given|\s+sex|$)', text, re.IGNORECASE)
            given = re.search(r'given\s*name[\s:]+([a-z\s-]+?)(?=\s+sex|$)', text, re.IGNORECASE)
            if surname and given:
                id_info['full_name'] = f"{surname.group(1).strip().title()} {given.group(1).strip().title()}"
        
        # Fallback for name extraction if not found by specific patterns
        if not id_info.get('full_name'):
            if id_info['document_type'] == 'huduma_card':
                # Look for name patterns common in Huduma cards
                name_match = re.search(r'names?[\s:]*([a-z\s]+?)(?=date\s*of\s*birth|dob|sex|$)', text, re.IGNORECASE)
                if name_match:
                    id_info['full_name'] = ' '.join([word.capitalize() for word in name_match.group(1).strip().split()])
            else:
                # Fallback for national ID
                name_match = re.search(r'(?:id\s*[a-z0-9\s]+)([a-z\s]+?)(?=date\s*of\s*birth|dob|$)', text, re.IGNORECASE)
                if name_match:
                    id_info['full_name'] = ' '.join([word.capitalize() for word in name_match.group(1).split()])
        
        # Extract Date of Birth
        dob_match = re.search(r'(?:date\s*of\s*birth|siku\s*ya\s*kuzaliwa|dob)[\s:]+([0-9]{1,2}[.\-/][0-9]{1,2}[.\-/][0-9]{2,4})', text, re.IGNORECASE)
        if dob_match:
            id_info['date_of_birth'] = dob_match.group(1).replace(' ', '')
        
        # Extract Gender
        gender_match = re.search(r'(?:sex|jinsia)\s*[\s:]+(male|female|m|f|man|woman|mwanaume|mwanamke)', text, re.IGNORECASE)
        if gender_match:
            gender = gender_match.group(1).lower()
            id_info['gender'] = 'Male' if gender in ['m', 'male', 'man', 'mwanaume'] else 'Female'
        
        # Extract Nationality (for national ID)
        nat_match = re.search(r'nationality\s*[\s:]+([a-z\s]+?)(?=\s+[a-z]+\s*[\s:]|$)', text, re.IGNORECASE)
        if nat_match:
            id_info['nationality'] = nat_match.group(1).strip().title()
        
        # Extract District of Birth
        district_match = re.search(r'(?:district\s*of\s*birth|birth\s*district|place\s*of\s*birth|mkoa\s*wa\s*kuzaliwa)\s*[\s:]+([a-z\s]+?)(?=\s+[a-z]+\s*[\s:]|$)', text, re.IGNORECASE)
        if district_match:
            id_info['district_of_birth'] = district_match.group(1).strip().title()
        
        # Extract Place of Issue
        place_match = re.search(r'(?:place\s*of\s*issue|issued\s*at|issue\s*place|mkoa\s*wa\s*utoaji)\s*[\s:]+([a-z\s]+?)(?=\s+[a-z]+\s*[\s:]|$)', text, re.IGNORECASE)
        if place_match:
            id_info['place_of_issue'] = place_match.group(1).strip().title()
        
        # Extract Date of Issue
        issue_date_match = re.search(r'(?:date\s*of\s*issue|issued\s*on|tarehe\s*ya\s*kuandikishwa)[\s:]+([0-9]{1,2}[.\-/][0-9]{1,2}[.\-/][0-9]{2,4})', text, re.IGNORECASE)
        if issue_date_match:
            id_info['date_of_issue'] = issue_date_match.group(1).replace(' ', '')
        
        # Extract Expiry Date (for national ID)
        expiry_match = re.search(r'(?:date\s*of\s*expiry|expiry\s*date|tarehe\s*ya\s*kuisha)[\s:]+([0-9]{1,2}[.\-/][0-9]{1,2}[.\-/][0-9]{2,4}|[a-z]+\s*[0-9]{1,2}[.\-/][0-9]{2,4})', text, re.IGNORECASE)
        if expiry_match:
            id_info['expiry_date'] = expiry_match.group(1).replace(' ', '')
        
        return {k: v for k, v in id_info.items() if v is not None}
        
    except Exception as e:
        # Return partial information if any error occurs during parsing
        id_info['error'] = f"Error during parsing: {str(e)}"
        return {k: v for k, v in id_info.items() if v is not None}

# Add regex module import at the top of the file
