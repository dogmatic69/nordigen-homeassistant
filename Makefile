.PHONY: build
build:
	rm dist/* || true
	python setup.py sdist

.PHONY: isort
isort:
	isort ./custom_components/nordigen ./tests --check-only

.PHONY: black
black:
	black --check ./custom_components/nordigen ./tests

.PHONY: flake8
flake8:
	flake8 ./custom_components/nordigen ./tests

.PHONY: test
test:
	pytest -vv -x

.PHONY: ci
ci: isort black flake8 test

.PHONY: ci-fix
ci-fix:
	isort ./custom_components/nordigen ./tests
	black ./custom_components/nordigen ./tests

.PHONY: dev
dev:
	$(MAKE) ci-fix
	$(MAKE) ci

.PHONY: install-pip
install-pip:
	python -m pip install --upgrade pip==20.2

.PHONY: install-dev
install-dev: install-pip
	pip install -e ".[dev]"

.PHONY: install-publish
install-publish: install-pip
	pip install -e ".[publish]"

.PHONY: publish
publish: build
	twine upload --verbose dist/*

