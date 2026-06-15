# Agent image — build context is the REPO ROOT (it needs agent/ + tools/ + skills/).
#   docker build -f deploy/agent.Dockerfile -t hh-agent .
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL} PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

COPY agent/requirements.txt agent/requirements.txt
RUN pip install --no-cache-dir -r agent/requirements.txt

COPY agent/ agent/
COPY tools/ tools/
COPY skills/ skills/

EXPOSE 9000

# LangGraph agent service: Q&A + manual pipeline triggers
CMD ["uvicorn", "agent.service:app", "--host", "0.0.0.0", "--port", "9000"]
