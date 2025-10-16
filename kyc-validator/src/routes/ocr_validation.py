from flask import Blueprint, request, jsonify
from services.ocr_service import extract_text_easyocr, parse_id_info


ocr_bp = Blueprint("ocr_validation", __name__)

@ocr_bp.route("/extract-text", methods=["POST"])
def extract_text():
    """
    Extract and parse information from an uploaded ID image.
    Returns structured data from the ID card.
    """
    if "image" not in request.files:
        return jsonify({"error": "Please upload an image file"}), 400

    image_bytes = request.files["image"].read()

    try:
        # Extract text using EasyOCR
        ocr_text = extract_text_easyocr(image_bytes)
        
        # Parse the extracted text into structured data
        parsed_data = parse_id_info(ocr_text)
        
        return jsonify({
            "success": True,
            "data": parsed_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Error processing ID card"
        }), 500
