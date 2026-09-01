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

# ----- Codebase Loader -----

def load_codebase(dir_path: str) -> dict[str, str]:
    codebase: dict[str, str] = {}
    path = Path(dir_path)
    for file in sorted(path.glob("*.py")):
        codebase[file.name] = file.read_text(encoding="utf-8")
    print(f"Loaded {len(codebase)} files for review: {list(codebase.keys())}")
    return codebase

# ----- Single-Pass Review -----

def single_pass_review(codebase: dict[str, str]) -> str:
    """
    Send all files in a single prompt and return the raw response text.
    This is the baseline — attention dilution is observable in the raw output.
    """
    all_code = "\n\n".join(
        f"=== {name} ===\n{content}"
        for name, content in codebase.items()
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        messages=[{
            "role": "user",
            "content": (
                "Review all files for bugs, style issues, and security vulnerabilities. "
                "Provide specific line references for each issue.\n\n"
                f"{all_code}"
            ),
        }],
    )

    # model may return thinking blocks — we only want text blocks
    return next(
        (block.text for block in response.content if block.type == "text"), ""
    )

# ----- Smoke Test -----

if __name__ == "__main__":
    sample_dir = Path(__file__).parent / "sample_code"
    codebase = load_codebase(str(sample_dir))

    print("\n" + "="*60)
    print("SINGLE-PASS REVIEW — Raw Response")
    print("="*60)
    raw_review = single_pass_review(codebase)
    print(raw_review)

    # Record issue counts per file by counting mentions
    print("\n" + "="*60)
    print("ISSUE MENTION COUNT PER FILE (attention dilution indicator)")
    print("="*60)
    for filename in codebase:
        count = raw_review.lower().count(filename.lower())
        print(f"  {filename}: mentioned {count} time(s)")
