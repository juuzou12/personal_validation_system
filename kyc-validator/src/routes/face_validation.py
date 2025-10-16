from flask import Blueprint, request, jsonify
from services.face_service import compare_faces

face_bp = Blueprint("face_validation", __name__)

@face_bp.route("/validate-face", methods=["POST"])
def validate_face():
    """
    Compare two uploaded face images (e.g., selfie and ID photo).
    """
    if "image1" not in request.files or "image2" not in request.files:
        return jsonify({"error": "Please upload both image1 and image2"}), 400

    image1 = request.files["image1"].read()
    image2 = request.files["image2"].read()

    try:
        match = compare_faces(image1, image2)
        return jsonify({
            "match": match,
            "message": "Faces match" if match else "Faces do not match"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
