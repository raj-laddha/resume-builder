# Use official Python image
FROM python:3.9-slim

# Set work directory
WORKDIR /app

# Copy backend and frontend code
COPY backend/ backend/
COPY frontend/ frontend/
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Set environment variables (override in docker-compose or at runtime)
ENV PYTHONUNBUFFERED=1

# Run the app with Uvicorn
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"] 