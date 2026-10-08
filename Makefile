.PHONY: install data train eval test lint clean

install:
	uv sync --all-packages

data:
	uv run recsys download
	uv run recsys prepare

train:
	uv run recsys train-all

eval:
	uv run recsys evaluate --models popularity,item_knn,funk_svd

test:
	uv run pytest ml/tests -q

lint:
	uv run ruff check .
	uv run ruff format --check .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
