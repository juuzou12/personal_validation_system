from flask import Blueprint, request, jsonify
from services.phone_service import validate_phone_number

phone_bp = Blueprint("phone_validation", __name__)

@phone_bp.route("/validate-phone", methods=["POST"])
def validate_phone():
    """
    Validate phone numbers and return region + carrier details.
    Example request: {"phone_number": "+254712345678"}
    """
    data = request.get_json()
    if not data or "phone_number" not in data:
        return jsonify({"error": "Please provide 'phone_number' in the JSON body"}), 400

    phone_number = data["phone_number"]
    region = data.get("region", "KE")

    result = validate_phone_number(phone_number, region)
    return jsonify(result), 200
