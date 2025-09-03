# Build stage for React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
# Build only if build directory doesn't exist (use pre-built if available)
RUN if [ ! -d "build" ]; then npm run build; fi

# Runtime stage
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt backend/requirements_simple.txt ./
# Install base dependencies first
RUN pip install --no-cache-dir -r requirements_simple.txt
# Then install ADK dependencies
RUN pip install --no-cache-dir google-genai>=0.4.0 googlemaps>=4.10.0 google-adk>=1.11.0 || echo "ADK installation failed, continuing..."

# Copy backend code
COPY backend/ ./backend/

# Copy config directory (includes database_manifest.py)
COPY config/ ./config/

# Copy ADK agent code
COPY agents/nj_voter_chat_adk/ ./agents/nj_voter_chat_adk/

# Copy scripts directory (contains PDL enrichment pipeline needed by agent)
COPY scripts/ ./scripts/

# Copy frontend build from previous stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0
ENV DEBUG=False
ENV GOOGLE_CLOUD_PROJECT=proj-roth
ENV GOOGLE_CLOUD_REGION=us-central1

# Create a non-root user and set permissions
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app
USER appuser

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "backend/main.py"]