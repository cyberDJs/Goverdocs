.PHONY: install verify test lint typecheck health index

install:
	./scripts/bootstrap_local.sh

verify:
	./scripts/verify.sh

test:
	.venv/bin/pytest

lint:
	.venv/bin/ruff check src tests

typecheck:
	.venv/bin/mypy src

health:
	.venv/bin/goverdocs health --root .

index:
	.venv/bin/goverdocs rebuild-index --root .
