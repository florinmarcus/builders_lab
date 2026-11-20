# MCP server image. Built on the server by deploy/scripts/upgrade.sh (tag = git commit).
FROM public.ecr.aws/docker/library/python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    MOCK_DIR=/app/system/data/mock RAG_PARENT_DIR=/app/system

WORKDIR /app
COPY pyproject.toml ./
COPY system/api ./system/api
# Optional extra CA certificate for builds behind a TLS-inspecting proxy (not used on the server):
#   docker build --secret id=extra_ca,src=/path/ca.crt .
RUN --mount=type=secret,id=extra_ca,required=false \
    if [ -f /run/secrets/extra_ca ]; then export PIP_CERT=/run/secrets/extra_ca; fi; \
    pip install --no-cache-dir ".[demo,gmail]" && rm -rf /root/.cache

# Mock data (seed) and the corpus session's rag package, if present
COPY system/data/mock ./system/data/mock
COPY system/rag ./system/rag

RUN useradd --system --uid 10001 --no-create-home app && mkdir -p /data/mail && chown app /data/mail
USER app

EXPOSE 8000
CMD ["python", "-m", "builders_api.mcp_server"]
