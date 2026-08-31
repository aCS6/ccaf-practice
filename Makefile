.PHONY: help

# Default target
help:
	@echo "Usage:"
	@echo "  make <chapter>-<exercise>-<task>"
	@echo ""
	@echo "Examples:"
	@echo "  make 1-1-1   -> uv run chapter-1/excercise-1/task-1.py"
	@echo "  make 1-1-2   -> uv run chapter-1/excercise-1/task-2.py"
	@echo "  make 2-3-1   -> uv run chapter-2/excercise-3/task-1.py"

# Pattern: <chapter>-<exercise>  (runs task-1.py by default)
%:
	@chapter=$$(echo "$@" | cut -d'-' -f1); \
	exercise=$$(echo "$@" | cut -d'-' -f2); \
	task=$$(echo "$@" | cut -d'-' -f3); \
	if [ -z "$$task" ]; then \
		echo "Error: use format make <chapter>-<exercise>-<task>, e.g. make 1-1-1"; exit 1; \
	fi; \
	path="chapter-$$chapter/excercise-$$exercise/task-$$task.py"; \
	if [ ! -f "$$path" ]; then \
		echo "Error: $$path not found"; exit 1; \
	fi; \
	echo "Running $$path ..."; \
	uv run "$$path"
