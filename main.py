# main.py

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn

app = FastAPI(
    title="Kenyan ID Validation System",
    description="API for validating Kenyan national IDs with facial recognition",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.endpoints import validation
app.include_router(validation.router)

@app.get("/")
async def root():
    return {"message": "Kenyan ID Validation System is running"}


@app.post("/validate-id")
async def validate_id(
    name: str = Form(...),
    id_number: str = Form(...),
    phone_number: str = Form(...),
    selfie: UploadFile = File(...),
    id_front: UploadFile = File(...),
    id_back: UploadFile = File(...)
):
    """
    Validate Kenyan ID with provided details and images
    """
    # TODO: Implement validation logic
    return {
        "status": "success",
        "message": "Validation endpoint is under construction",
        "data": {
            "name": name,
            "id_number": id_number,
            "phone_number": phone_number,
            "files_received": [
                selfie.filename,
                id_front.filename,
                id_back.filename
            ]
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)