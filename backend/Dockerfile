FROM python:3.9-slim
WORKDIR /app
COPY api.py .
RUN pip install fastapi uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

