# Production Dockerfile for ViralReel AI on Hugging Face Spaces & Cloud
FROM python:3.11-slim

# Install system dependencies & native FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set up non-root user (Standard for Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Install Python requirements
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code and assets
COPY --chown=user:user . .

# Ensure data directories exist
RUN mkdir -p data/downloads data/processed data/sessions

# Hugging Face Spaces listens on port 7860
ENV HOST=0.0.0.0 \
    PORT=7860 \
    PYTHONUNBUFFERED=1

EXPOSE 7860

# Start background bot & web control server
CMD ["python", "run.py"]
