# ClauseTrace backend (deploy support, backend lane).
# Build from the repo root so corpus/ and scripts/ are available:
#   docker build -f backend/Dockerfile -t clausetrace-backend .
# Or `docker compose up --build` from the repo root (recommended:
# provisions Postgres + FalkorDB alongside the API).
FROM python:3.12-slim

# poppler-utils provides `pdftoppm` for scan/vision intake.
RUN apt-get update \
    && apt-get install -y --no-install-recommends poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /repo/backend
COPY --chown=app:app backend/pyproject.toml ./
COPY --chown=app:app backend/app ./app
COPY --chown=app:app backend/checker ./checker
COPY --chown=app:app corpus /repo/corpus
COPY --chown=app:app scripts /repo/scripts

# prod extras: psycopg (Postgres), pypdf (PDF text layer), falkordb (graph projection).
RUN pip install --no-cache-dir .[prod]

RUN useradd -m app && mkdir -p /data && chown app:app /data
USER app

ENV API_STUB=0 LLM_MODE=replay DEMO_MODE=1
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"

# Seed the demo database on boot (SQLite file or CLAUSETRACE_DB_URL Postgres;
# seed_demo.py prefers the URL when set), then serve.
CMD ["sh", "-c", "python /repo/scripts/seed_demo.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
