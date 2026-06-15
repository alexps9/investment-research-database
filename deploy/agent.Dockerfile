# Agent image — build context is the REPO ROOT (it needs agent/ + tools/ + skills/).
#   docker build -f deploy/agent.Dockerfile -t hh-agent .
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL} PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# Install deps first (better layer caching).
COPY agent/requirements.txt agent/requirements.txt
COPY agent/alert_agent/requirements.txt agent/alert_agent/requirements.txt
COPY agent/digest_agent/requirements.txt agent/digest_agent/requirements.txt
RUN pip install --no-cache-dir \
    -r agent/requirements.txt \
    -r agent/alert_agent/requirements.txt \
    -r agent/digest_agent/requirements.txt

# App code (the three top-level packages the agent imports).
COPY agent/ agent/
COPY tools/ tools/
COPY skills/ skills/

# Idle by default — the agent runs on demand:
#   docker compose run --rm agent python -m agent.main "..."
#   docker compose exec agent python -m agent.digest_agent.pipeline
CMD ["tail", "-f", "/dev/null"]
