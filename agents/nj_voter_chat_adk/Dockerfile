# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements early to leverage layer caching
COPY agents/nj_voter_chat_adk/requirements.txt /app/agents/nj_voter_chat_adk/requirements.txt

RUN pip install --no-cache-dir -r /app/agents/nj_voter_chat_adk/requirements.txt

# Copy only what we need to run the app
COPY agents /app/agents

ENV PYTHONPATH=/app

# Cloud Run provides $PORT (defaults to 8080)
ENV PORT=8080

EXPOSE 8080

CMD ["bash", "-lc", "streamlit run agents/nj_voter_chat_adk/app_streamlit.py --server.port $PORT --server.address 0.0.0.0"]
