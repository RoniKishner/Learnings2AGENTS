.PHONY: install run test clean lint dry-run

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Usage:
#   make run CSV=/path/to/learnings.csv TARGET=/path/to/checked-out/repo
#   make run CSV=... TARGET=... REPOSITORY=my-repo MODEL=gemini-2.5-flash
#   make dry-run CSV=... TARGET=...
#
# GEMINI_API_KEY (optional): never pass it as a plain CLI argument. Export it
# as an environment variable instead — e.g. `export GEMINI_API_KEY=...` in
# your shell, a .env loaded by direnv, or a GitHub Actions `env:` block
# sourced from a GitHub Environment secret (${{ secrets.GEMINI_API_KEY }}).
# GNU Make automatically forwards environment/command-line variables into
# recipe subshells, so `learnings2agents` picks it up via os.environ without
# it ever needing to appear in a Makefile recipe. The `run`/`dry-run` recipes
# below are also silenced (@) so no expanded command line (which could
# otherwise contain secrets) is ever echoed to the terminal or CI logs.

$(VENV)/bin/activate: requirements.txt pyproject.toml
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	touch $(VENV)/bin/activate

install: $(VENV)/bin/activate

run: install
	@$(PYTHON) -m learnings2agents.cli \
		--csv "$(CSV)" \
		--target "$(TARGET)" \
		$(if $(REPOSITORY),--repository "$(REPOSITORY)",) \
		$(if $(MODEL),--model "$(MODEL)",) \
		$(EXTRA_ARGS)

dry-run: install
	@$(PYTHON) -m learnings2agents.cli \
		--csv "$(CSV)" \
		--target "$(TARGET)" \
		$(if $(REPOSITORY),--repository "$(REPOSITORY)",) \
		$(if $(MODEL),--model "$(MODEL)",) \
		--dry-run -v

test: install
	$(PYTHON) -m pytest -q

lint: install
	$(PYTHON) -m py_compile src/learnings2agents/*.py

clean:
	rm -rf $(VENV) .learnings2agents_cache
	find . -type d -name "__pycache__" -not -path "./$(VENV)/*" -exec rm -rf {} +
