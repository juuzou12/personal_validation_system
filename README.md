# Kenyan ID Validation System

A FastAPI-based service for validating Kenyan national IDs using facial recognition and OCR.

## Features

- Kenyan ID number validation
- Face matching between selfie and ID photo
- OCR for extracting text from ID cards
- Phone number validation
- RESTful API with OpenAPI documentation

## Prerequisites

- Python 3.8+
- Tesseract OCR (for text extraction)
- OpenCV and other Python dependencies (installed via `requirements.txt`)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd personal_validation_system
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Tesseract OCR:
   - **macOS**: `brew install tesseract`
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Copy the example environment file and update it:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Running the Application

1. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```

2. Access the API documentation at:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Validate Kenyan ID

```http
POST /api/validate/kenyan-id
```

**Form Data:**
- `name`: Full name as per ID
- `id_number`: Kenyan national ID number
- `phone_number`: Phone number with country code (e.g., +254...)
- `selfie`: Selfie image file
- `id_front`: Front side of ID card image
- `id_back`: Back side of ID card image

**Example Response:**
```json
{
  "status": "success",
  "message": "Validation completed successfully",
  "is_verified": true,
  "data": {
    "name": "John Doe",
    "id_number": "12345678",
    "phone_number": "+254712345678"
  },
  "validation_details": {
    "id_validation": {
      "id_number_valid": true,
      "id_pattern_matched": true,
      "extracted_data": {
        "id_number": "12345678",
        "full_name": "John Doe",
        "date_of_birth": "1990-01-01",
        "gender": "Male",
        "other_details": {}
      }
    },
    "face_match": {
      "is_match": true,
      "confidence": 98.5,
      "message": "Faces match with 98.5% confidence"
    },
    "phone_validation": {
      "is_valid": true,
      "message": "Valid phone number",
      "normalized_number": "+254712345678"
    },
    "name_match": true,
    "ocr_extracted_data": {
      "id_number": "12345678",
      "full_name": "John Doe",
      "date_of_birth": "1990-01-01",
      "gender": "Male",
      "other_details": {}
    }
  }
}
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
```

### Linting

```bash
flake8
```

## Deployment

For production deployment, consider using:

1. Gunicorn with Uvicorn workers:
   ```bash
   gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 main:app
   ```

2. Docker (create a `Dockerfile`):
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       tesseract-ocr \
       libgl1-mesa-glx \
       && rm -rf /var/lib/apt/lists/*
   
   # Install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy application code
   COPY . .
   
   # Run the application
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

## License

MIT
