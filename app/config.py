import os
from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Kenyan ID Validation API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]
    
    # Face recognition settings
    FACE_MATCH_THRESHOLD: float = 0.6  # Lower is more strict
    
    # OCR settings
    USE_GPU: bool = os.getenv("USE_GPU", "False").lower() in ("true", "1", "t")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()
