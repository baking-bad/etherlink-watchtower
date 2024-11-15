.ONESHELL:
.DEFAULT_GOAL: all

py := uv run

source_dir := .


install:
	uv sync --dev --no-install-project

ssort:
	$(py) ssort $(source_dir)

black:
	$(py) black $(source_dir)

ruff:
	$(py) ruff check --fix-only --show-fixes $(source_dir)

mypy:
	$(py) mypy $(source_dir)

lint: ssort black ruff mypy
