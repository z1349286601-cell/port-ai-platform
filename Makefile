.PHONY: setup dev test docker-up docker-down clean

PYTHON := python
PIP := pip

setup:
	cd backend && $(PIP) install -r requirements.txt
	cd frontend && npm install

dev:
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --port 8000 &
	cd frontend && npm run dev &
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "Swagger: http://localhost:8000/docs"

dev-backend:
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && $(PYTHON) -m pytest -v

docker-up:
	docker compose up -d

docker-down:
	docker compose down

data-init:
	cd backend && $(PYTHON) ../scripts/init_demo_data.py

data-ingest:
	cd backend && $(PYTHON) ../scripts/ingest_documents.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf backend/data/ logs/
