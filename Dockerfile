# NFT Batch Minter Docker Image
# Multi-stage build for smaller final image

# Build stage
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ ./src/
COPY main.py ./
COPY config.example.json ./

# Create necessary directories
RUN mkdir -p logs abi output

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Volume for configuration and logs
VOLUME ["/app/config", "/app/logs", "/app/abi"]

# Default command (can be overridden)
CMD ["python", "main.py", "-c", "/app/config/config.json"]