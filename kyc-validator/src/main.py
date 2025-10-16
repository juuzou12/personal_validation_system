from flask import Flask
from routes.health import health_bp
from routes.face_validation import face_bp
from routes.ocr_validation import ocr_bp
from routes.phone_validation import phone_bp
from routes.kyc import kyc_bp
def create_app():
    app = Flask(__name__)

    # Register routes
    app.register_blueprint(health_bp)
    app.register_blueprint(face_bp)
    app.register_blueprint(ocr_bp)
    app.register_blueprint(phone_bp)
    app.register_blueprint(kyc_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
