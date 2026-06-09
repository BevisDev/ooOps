FROM python:3.12.13-slim

ENV DEBIAN_FRONTEND=noninteractive

LABEL maintainer="dev.binhtt@gmail.com"

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    bash \
    openssh-client \
    ca-certificates \
    curl \
    make \
    jq \
    yq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    ruff==0.15.13 \
    pytest==9.0.3

RUN groupadd -g 1000 appuser \
    && useradd -u 1000 -g appuser -m appuser \
    && chown -R appuser:appuser /home/appuser
    
ENV HOME=/home/appuser
    
USER appuser

WORKDIR $HOME

CMD ["bash"]
