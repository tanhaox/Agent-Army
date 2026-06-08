FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (prefer offline packages, auto-fallback to PyPI)
COPY requirements.txt .
COPY offline_packages/ /tmp/packages/
RUN pip install --no-cache-dir --find-links=/tmp/packages -r requirements.txt \
    && rm -rf /tmp/packages

# Install Playwright browsers (Chromium only)
RUN playwright install chromium && \
    playwright install-deps chromium || true

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/uploads /app/logs /app/models /app/voice_profiles

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
