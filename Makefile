.PHONY: help

# Default target
help:
	@echo "Usage:"
	@echo "  make <chapter>-<exercise>"
	@echo ""
	@echo "Examples:"
	@echo "  make 1-1   -> uv run chapter-1/excercise-1/task-1.py"
	@echo "  make 1-2   -> uv run chapter-1/excercise-2/task-1.py"
	@echo "  make 2-1   -> uv run chapter-2/excercise-1/task-1.py"

%:
	@input="$@"; \
	case "$$input" in \
		*-*) ;; \
		*) echo "Error: use format make <chapter>-<exercise>, e.g. make 1-1"; exit 1 ;; \
	esac; \
	chapter=$$(echo "$$input" | cut -d'-' -f1); \
	exercise=$$(echo "$$input" | cut -d'-' -f2); \
	path="chapter-$$chapter/excercise-$$exercise/task-1.py"; \
	if [ ! -f "$$path" ]; then \
		echo "Error: $$path not found"; exit 1; \
	fi; \
	echo "Running $$path ..."; \
	uv run "$$path"
