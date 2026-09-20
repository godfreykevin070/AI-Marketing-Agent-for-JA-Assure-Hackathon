.PHONY: api ui install dev seed test fmt

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

api:
	cd backend && uvicorn app.main:app --reload --port 8000

ui:
	cd frontend && npm run dev

dev:
	$(MAKE) -j2 api ui

seed:
	cd backend && python -m app.seed

test:
	cd backend && pytest -q

fmt:
	cd backend && ruff check --fix . || true
	cd frontend && npm run lint --if-present