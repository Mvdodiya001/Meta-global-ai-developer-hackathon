# ClauseTrace backend (T8.2 deploy support, backend lane).
# Build from the repo root so corpus/ and scripts/ are available:
#   docker build -f backend/Dockerfile -t clausetrace-backend .
FROM python:3.12-slim

WORKDIR /repo/backend
COPY backend/pyproject.toml ./
COPY backend/app ./app
COPY backend/checker ./checker
COPY corpus /repo/corpus
COPY scripts /repo/scripts

RUN pip install --no-cache-dir .

ENV API_STUB=0 LLM_MODE=replay DEMO_MODE=1 CLAUSETRACE_DB=/data/db.sqlite3
VOLUME ["/data"]
EXPOSE 8000

# Seed the demo database on first boot, then serve.
CMD ["sh", "-c", "python /repo/scripts/seed_demo.py --db \"$CLAUSETRACE_DB\" && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
