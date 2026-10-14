.PHONY: setup up run test lint

setup:   ## Cria o ambiente virtual e instala o projeto
	python -m venv .venv && .venv/bin/pip install -e ".[dev]"

up:      ## Sobe o PostgreSQL
	docker compose up -d --wait

run:     ## Carga incremental de todas as séries
	set -a && . ./.env && set +a && .venv/bin/python -m bcb_etl

test:    ## Testes (os de integração usam o banco do docker compose)
	set -a && . ./.env && set +a && .venv/bin/pytest -v

lint:
	.venv/bin/ruff check .
