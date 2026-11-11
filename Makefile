.PHONY: setup data db analyze test api web chain all clean

# Default target
all: setup data db analyze test chain web
	@echo "=============================="
	@echo " PHANTOM Build Complete"
	@echo "=============================="
	python scripts/e2e_demo.py

# Setup: install all dependencies
setup: setup-python setup-node setup-blockchain

setup-python:
	cd analytics && python -m pip install -r requirements.txt -q

setup-node:
	cd frontend && npm install --legacy-peer-deps

setup-blockchain:
	cd blockchain && npm install

# Data: run PaySim adapter or generate fixture
data:
	python scripts/paysim_adapter.py --target 70000
	python scripts/generate_demo_data.py

# Database: validate SQL, seed data
db:
	python scripts/seed_supabase.py

# Analyze: run risk analysis
analyze:
	python scripts/run_risk_analysis.py
	python analytics/evaluation/evaluate.py

# Test: run all tests
test: test-python test-blockchain test-frontend

test-python:
	cd analytics && python -m pytest tests/ -v

test-blockchain:
	cd blockchain && npx hardhat test

test-frontend:
	cd frontend && npm run typecheck && npm run build

# API: start the analytics service
api:
	cd analytics && uvicorn app.main:app --reload --port 8000

# Web: build frontend
web:
	cd frontend && npm run build

# Blockchain: compile and test contracts
chain:
	cd blockchain && npx hardhat compile && npx hardhat test

# Clean: remove build artifacts
clean:
	rm -rf frontend/dist analytics/__pycache__ blockchain/artifacts blockchain/cache

