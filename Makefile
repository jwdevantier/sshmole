.DEFAULT_GOAL := help
.PHONY: help
help:
	@echo "\033[33mAvailable targets, for more information, see \033[36mREADME.md\033[0m"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## install package for local user
	pip install --user .

.PHONY: uninstall
uninstall: ## uninstall package for local user
	pip uninstall sshmole || 0

.PHONY: _venv
_venv:
	test -d .venv || python3 -m venv .venv ;\
		. .venv/bin/activate ;\
		pip install -Ur requirements.txt

.PHONY: venv
venv: ## create virtualenv (in 'venv') if needed
	test -d .venv || make _venv

.PHONY: dev-setup
dev-setup: venv ## install package in editable mode (console scripts defined in setup.py are available)
	. .venv/bin/activate ;\
		pip install -e .