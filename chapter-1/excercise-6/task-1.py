import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    auth_token=os.environ["ANTHROPIC_API_KEY"],
    base_url=os.environ.get("ANTHROPIC_BASE_URL"),
)
MODEL = "claude-opus-4-8"

def load_codebase(dir_path: str) -> dict[str, str]:
    codebase: dict[str, str] = {}
    path = Path(dir_path)
    for file in sorted(path.glob("*.py")):
        codebase[file.name] = file.read_text(encoding="utf-8")
    print(f"Loaded {len(codebase)} files for review: {list(codebase.keys())}")
    return codebase

if __name__ == "__main__":
    sample_dir = Path(__file__).parent / "sample_code"
    codebase = load_codebase(str(sample_dir))
    print(f"\nTotal files: {len(codebase)}")
    for name, content in codebase.items():
        print(f"  {name}: {len(content.splitlines())} lines")
