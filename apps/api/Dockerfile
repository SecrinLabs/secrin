# API Application Docker Container
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
  curl \
  git \
  postgresql-client \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary packages and API code
COPY packages/ ./packages/
COPY apps/api/ ./apps/api/

# Create necessary directories
RUN mkdir -p chroma_store logs

# Expose port
EXPOSE 8000

# Start the API server
CMD ["uvicorn", "apps.api.index:app", "--host", "0.0.0.0", "--port", "8000"]
