# Claude Certified Architect (Foundations) - Practice Tasks

Practice exercises for the [Claude Certified Architect (Foundations) exam](https://claudecertificationguide.com/learn). This repository contains the code solutions for hands-on exercises — the theory material is not included.

**Credit:** Theory from [claudecertificationguide.com/learn](https://claudecertificationguide.com/learn)
**Practice source:** [claudecertificationguide.com/learn/exercises](https://claudecertificationguide.com/learn/exercises)

## Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- An Anthropic API key (or compatible endpoint)

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd anthropic-certification-excercise

# Install dependencies
uv sync

# Set up your API key
cp .env.example .env  # then edit .env with your key
```

## Project Structure

```
.
├── chapter-1/
│   └── excercise-1/
│       └── task-1.py    # Tool use: calculator + web search agent
└── main.py
```

## Running

```bash
uv run main.py
```

## VS Code Setup

Press `Ctrl+S` to auto-sort Python imports. Install these extensions:

- `ms-python.isort`
- `ms-python.black-formatter`

## License

For personal study use only.
