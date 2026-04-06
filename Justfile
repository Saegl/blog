dev:
    (until curl -s -o /dev/null http://127.0.0.1:8000; do sleep 0.2; done && xdg-open http://127.0.0.1:8000) &
    uv run fastapi dev

run:
    uv run fastapi run

fmt:
    uv run ruff format .

lint:
    uv run ruff check .

deploy:
    ssh root@saegl.me deploy-blog
