FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    ca-certificates \
    curl \
    make \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*