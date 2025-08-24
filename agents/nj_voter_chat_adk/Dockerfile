# This Dockerfile is deprecated - use the main application Dockerfile instead
# The agent is now integrated into the backend API service
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY agents/nj_voter_chat_adk/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --verbose -r /app/requirements.txt

# Copy all agent files
COPY agents/nj_voter_chat_adk/ /app/agents/nj_voter_chat_adk/

# Set up parent directory structure for imports
RUN mkdir -p /app/agents && touch /app/agents/__init__.py

ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

# Run CLI for testing purposes only
CMD ["python", "-m", "agents.nj_voter_chat_adk.app_cli"]