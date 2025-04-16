FROM python:3.9-slim

WORKDIR /app

# Install system packages needed for OpenCV
RUN apt-get update && \
    apt-get install -y gcc libgl1 && \
    rm -rf /var/lib/apt/lists/*

# Copy app code
COPY api.py .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install fastapi uvicorn opencv-python-headless numpy python-multipart

# Run backend
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]




