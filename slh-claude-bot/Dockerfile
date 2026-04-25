FROM python:3.11-slim

# Install git + curl + docker CLI (talks to host docker daemon via /var/run/docker.sock mount)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Railway CLI — install at first run via /railway_install command (network
# dependency at build time was unreliable). railway_ops.py auto-detects:
#   - if not installed → command returns friendly install instruction
#   - if installed     → all /railway_* commands work
# Operator can install once with: docker exec slh-claude-bot sh -c \
#   'curl -fsSL cli.new | bash -i' (or copy binary from host).

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Workspace will be mounted from host (D:\SLH_ECOSYSTEM) at /workspace
ENV WORKSPACE=/workspace
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
