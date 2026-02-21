dev:
    uv run fastapi dev

run:
    uv run fastapi run

fmt:
    uv run ruff format .

lint:
    uv run ruff check .
