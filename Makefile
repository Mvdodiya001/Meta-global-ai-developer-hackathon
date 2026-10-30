.PHONY: setup dev check check-backend check-frontend seed reset-demo record hooks status

# Starter Makefile. Muse Code extends it in T0.4 (backend targets). Human-only: `check`.

setup:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd frontend && npm install

dev:
	@echo "Run in two terminals: (1) cd backend && .venv/bin/uvicorn app.main:app --port 8000 --reload  (2) cd frontend && npm run dev"

check-backend:
	cd backend && .venv/bin/ruff check . && .venv/bin/mypy . && .venv/bin/pytest -q

check-frontend:
	cd frontend && npm run lint && npm run test -- --run

check: check-backend check-frontend

seed:
	cd backend && .venv/bin/python ../scripts/seed_demo.py

reset-demo:
	sh scripts/reset_demo.sh

record:
	cd backend && set -a; [ -f ../.env ] && . ../.env; set +a; LLM_MODE=live .venv/bin/python ../scripts/record_cassettes.py

# One-time, run by the human: installs git guards (human-only commits/pushes, no co-author lines).
hooks:
	git config core.hooksPath scripts/git-hooks
	chmod +x scripts/git-hooks/*
	git config alias.hc '!CT_HUMAN=1 git commit'
	git config alias.hp '!CT_HUMAN=1 git push'
	@echo "Hooks installed. Commit with: git hc -m \"message\"   Push with: git hp"

# Shows every logged task heading from the agent and human logs.
status:
	@grep -H "^## \\[T[0-9]" docs/logs/*.md || echo "No log entries yet."
