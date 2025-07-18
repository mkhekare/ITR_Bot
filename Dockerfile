# Base image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libmagic1 \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Create required directories with proper permissions
RUN mkdir -p /tmp/uploads && \
    mkdir -p /app/instance && \
    chmod -R 777 /tmp/uploads && \
    chmod -R 777 /app

# Install Gunicorn explicitly
RUN pip install gunicorn

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 7860

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV UPLOAD_FOLDER=/tmp/uploads
ENV INSTANCE_PATH=/app/instance

# Run the application using Python module syntax
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]