# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Avoid tzdata and other prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libsm6 \
    libxext6 \
    libxrender-dev \
    tesseract-ocr \
    libgl1 \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 5000

# Environment variables
ENV FLASK_APP=src/main.py
ENV FLASK_ENV=production

# Run the app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "src.main:app"]
