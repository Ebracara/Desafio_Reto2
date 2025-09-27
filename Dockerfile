
FROM python:3.12-slim-bookworm

# Set environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_PROJECT_ENVIRONMENT=/usr/local

# Install system dependencies (minimal for production)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv
RUN pip install --no-cache-dir uv


# Set working directory
WORKDIR /app

# Copy dependency files for better Docker layer caching
COPY pyproject.toml uv.lock* ./

# Install dependencies directly to system environment
RUN uv sync --frozen --no-dev && \
    rm -rf /root/.cache/uv

# Copy application code
COPY app/ ./app/
COPY *.py ./

# Running as root user (files owned by root by default)

# Expose ports
EXPOSE 8000 8501

# Default command
CMD ["uvicorn", "app.fast_main:app", "--host", "0.0.0.0", "--port", "8000"]