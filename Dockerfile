# DevSecrin - Developer Context Engine
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/packages

# Install system dependencies
RUN apt-get update && apt-get install -y \
  curl \
  git \
  postgresql-client \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Install Node.js and pnpm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && npm install -g pnpm

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY requirements.txt ./
COPY turbo.json ./

# Copy package configurations
COPY packages/*/package.json ./packages/*/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies
RUN pnpm install --frozen-lockfile

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p chroma_store logs

# Expose ports
EXPOSE 8000 3000

# Create startup script
RUN echo '#!/bin/bash\n\
  echo "🚀 Starting DevSecrin Developer Context Engine..."\n\
  echo "📦 Setting up environment..."\n\
  \n\
  # Run database migrations\n\
  echo "🗄️  Setting up database..."\n\
  python packages/dbup/runner.py\n\
  \n\
  # Start the application\n\
  echo "🚀 Starting application..."\n\
  pnpm run devsecrin\n\
  ' > /app/start.sh && chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["/app/start.sh"]
