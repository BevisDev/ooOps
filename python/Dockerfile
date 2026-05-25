FROM python:3.12.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    ca-certificates \
    curl \
    make \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    ruff==0.15.13 \
    pytest==9.0.3

WORKDIR /app