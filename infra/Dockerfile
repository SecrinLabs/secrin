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

# Copy the entire application structure
COPY api/ ./api/
COPY config/ ./config/
COPY engine/ ./engine/
COPY service/ ./service/
COPY migration/ ./migration/

# Create necessary directories for data persistence
RUN mkdir -p gemini_store chroma_store logs

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
  chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start the API server
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"]
