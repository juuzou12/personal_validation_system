import cv2
import numpy as np
import face_recognition
from typing import Tuple, Optional, Dict, Any
import logging
from pathlib import Path
import tempfile
import os

logger = logging.getLogger(__name__)

class ImageProcessingError(Exception):
    """Custom exception for image processing errors"""
    pass

def load_image(image_path: str) -> np.ndarray:
    """Load an image from file path or bytes"""
    try:
        if isinstance(image_path, (str, Path)):
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            image = cv2.imread(str(image_path))
        else:
            # Handle file-like object or bytes
            image_array = np.frombuffer(image_path.read(), np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to load image: Invalid image data")
            
        # Convert BGR to RGB (face_recognition uses RGB)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    except Exception as e:
        logger.error(f"Error loading image: {str(e)}")
        raise ImageProcessingError(f"Failed to load image: {str(e)}")

def detect_faces(image: np.ndarray) -> Tuple[bool, list]:
    """
    Detect faces in an image
    Returns:
        tuple: (success, face_locations) - success flag and list of face locations
    """
    try:
        # Convert to RGB (if not already)
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = image
        else:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        # Find all face locations in the image
        face_locations = face_recognition.face_locations(rgb_image)
        return len(face_locations) > 0, face_locations
    except Exception as e:
        logger.error(f"Error detecting faces: {str(e)}")
        return False, []

def compare_faces(known_image: np.ndarray, unknown_image: np.ndarray, tolerance: float = 0.6) -> Dict[str, Any]:
    """
    Compare faces in two images
    Returns:
        dict: {
            'is_match': bool,
            'confidence': float,
            'message': str
        }
    """
    try:
        # Find face encodings for both images
        known_encodings = face_recognition.face_encodings(known_image)
        unknown_encodings = face_recognition.face_encodings(unknown_image)
        
        if not known_encodings or not unknown_encodings:
            return {
                'is_match': False,
                'confidence': 0.0,
                'message': 'No faces found in one or both images'
            }
        
        # Compare the first face found in each image
        face_distance = face_recognition.face_distance([known_encodings[0]], unknown_encodings[0])[0]
        confidence = (1 - face_distance) * 100
        is_match = face_distance <= tolerance
        
        return {
            'is_match': is_match,
            'confidence': confidence,
            'message': f"Face match with {confidence:.2f}% confidence"
        }
    except Exception as e:
        logger.error(f"Error comparing faces: {str(e)}")
        return {
            'is_match': False,
            'confidence': 0.0,
            'message': f'Error comparing faces: {str(e)}'
        }

def preprocess_id_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess ID card image for better OCR results
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply dilation and erosion to remove noise
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.dilate(thresh, kernel, iterations=1)
        processed = cv2.erode(processed, kernel, iterations=1)
        
        return processed
    except Exception as e:
        logger.error(f"Error preprocessing ID image: {str(e)}")
        return image

def save_uploaded_file(upload_file, suffix: str = "") -> str:
    """
    Save uploaded file to a temporary location
    Returns the path to the saved file
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(upload_file.file.read())
            return temp_file.name
    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}")
        raise ImageProcessingError(f"Failed to save uploaded file: {str(e)}")

def cleanup_temp_file(file_path: str) -> None:
    """Remove temporary file if it exists"""
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logger.warning(f"Error removing temporary file {file_path}: {str(e)}")
