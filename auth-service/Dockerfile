FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copy dependency manifest first so dependency install can be cached.
COPY pyproject.toml uv.lock ./


RUN --mount=type=cache,id=pip-cache,target=/root/.cache/pip \
pip install .

# Copy only application code (build context is reduced by .dockerignore).
COPY . .

RUN chmod +x Entrypoint.sh

EXPOSE 8081

CMD ["./Entrypoint.sh"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]