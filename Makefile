.PHONY: install test demo

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

demo:
	./scripts/demo.sh
