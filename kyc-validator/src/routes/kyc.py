from flask import Blueprint, request, jsonify
import phonenumbers
import easyocr
import face_recognition
import numpy as np
from PIL import Image
import io
import re

kyc_bp = Blueprint('kyc', __name__)

reader = easyocr.Reader(['en'])

@kyc_bp.route('/api/validate-kyc', methods=['POST'])
def validate_kyc():
    try:
        # --- 1️⃣ Get Form Data ---
        name = request.form.get('name')
        id_number = request.form.get('id_number')
        phone_number = request.form.get('phone_number')

        selfie = request.files.get('selfie')
        id_front = request.files.get('id_front')
        id_back = request.files.get('id_back')

        if not all([name, id_number, phone_number, selfie, id_front, id_back]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        # --- 2️⃣ Phone validation ---
        try:
            parsed_phone = phonenumbers.parse(phone_number, None)
            is_valid_phone = phonenumbers.is_valid_number(parsed_phone)
            normalized_phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            is_valid_phone = False
            normalized_phone = None

        # --- 3️⃣ Read all file content into memory first ---
        selfie_content = selfie.read()
        id_front_content = id_front.read()
        id_back_content = id_back.read()

        # --- 4️⃣ OCR on ID front/back ---
        try:
            # Process front ID
            front_img = Image.open(io.BytesIO(id_front_content))
            ocr_text_front = " ".join(reader.readtext(np.array(front_img), detail=0))
            
            # Process back ID
            back_img = Image.open(io.BytesIO(id_back_content))
            ocr_text_back = " ".join(reader.readtext(np.array(back_img), detail=0))
            
            combined_text = (ocr_text_front + " " + ocr_text_back).upper()

            # Extract ID and name heuristically
            extracted_id_match = re.search(r'\b\d{7,8}\b', combined_text)
            extracted_name_match = re.search(r'(?:NAME|FULL NAMES?)[\s:]*([A-Z\s]+)(?=DATE|$|ID)', combined_text)

            extracted_data = {
                "id_number": extracted_id_match.group(0) if extracted_id_match else None,
                "full_name": extracted_name_match.group(1).strip().title() if extracted_name_match else name,
                "date_of_birth": None,
                "gender": None,
                "other_details": {}
            }

            id_pattern_matched = bool(extracted_id_match and id_number in extracted_id_match.group(0))
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error processing ID images: {str(e)}"
            }), 400

        # --- 5️⃣ Face recognition ---
        try:
            # Reload images for face recognition
            selfie_img = Image.open(io.BytesIO(selfie_content)).convert('RGB')
            id_img = Image.open(io.BytesIO(id_front_content)).convert('RGB')
            
            # Convert to numpy arrays
            selfie_array = np.array(selfie_img)
            id_array = np.array(id_img)
            
            # Get face encodings
            selfie_encodings = face_recognition.face_encodings(selfie_array)
            id_encodings = face_recognition.face_encodings(id_array)

            if not selfie_encodings or not id_encodings:
                face_match_result = False
                confidence = 0.0
                face_message = "No faces detected in one or both images"
            else:
                # Compare the first face found in each image
                match_results = face_recognition.compare_faces(
                    [id_encodings[0]], 
                    selfie_encodings[0]
                )
                face_distance = face_recognition.face_distance(
                    [id_encodings[0]], 
                    selfie_encodings[0]
                )[0]
                confidence = round((1 - face_distance) * 100, 2)
                face_match_result = bool(match_results[0])
                face_message = f"Faces match with {confidence}% confidence" if face_match_result else "Faces do not match"
                
        except Exception as e:
            face_match_result = False
            confidence = 0.0
            face_message = f"Error during face recognition: {str(e)}"
            
        # --- 6️⃣ Build response ---
        response = {
            "status": "success",
            "message": "Validation completed successfully",
            "is_verified": all([
                id_pattern_matched,
                face_match_result,
                is_valid_phone
            ]),
            "data": {
                "name": name,
                "id_number": id_number,
                "phone_number": normalized_phone or phone_number
            },
            "validation_details": {
                "id_validation": {
                    "id_number_valid": id_pattern_matched,
                    "id_pattern_matched": id_pattern_matched,
                    "extracted_data": extracted_data
                },
                "face_match": {
                    "is_match": face_match_result,
                    "confidence": confidence,
                    "message": face_message
                },
                "phone_validation": {
                    "is_valid": is_valid_phone,
                    "message": "Valid phone number" if is_valid_phone else "Invalid phone number",
                    "normalized_number": normalized_phone
                },
                "name_match": extracted_data["full_name"].lower() in name.lower(),
                "ocr_extracted_data": extracted_data
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred during validation: {str(e)}"
        }), 500
