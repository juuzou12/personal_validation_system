import face_recognition
from PIL import Image
import numpy as np
import io
import base64

def compare_faces(image1_bytes: bytes, image2_bytes: bytes) -> bool:
    """
    Compare two images and return True if they match.
    """
    # Load the images into numpy arrays
    image1 = face_recognition.load_image_file(io.BytesIO(image1_bytes))
    image2 = face_recognition.load_image_file(io.BytesIO(image2_bytes))

    # Encode the faces
    face1_encodings = face_recognition.face_encodings(image1)
    face2_encodings = face_recognition.face_encodings(image2)

    if not face1_encodings or not face2_encodings:
        return False  # No faces detected

    match_results = face_recognition.compare_faces([face1_encodings[0]], face2_encodings[0])
    return bool(match_results[0])  # Convert numpy.bool_ to Python bool
