import os
import re
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


def per_file_review(codebase: dict[str, str]) -> dict[str, list[dict]]:
    """
    Review each file individually — every file gets full attention budget.
    Returns structured results: {filename: [{"line": n, "severity": "...", "description": "..."}]}
    """
    results: dict[str, list[dict]] = {}

    for filename, content in codebase.items():
        print(f"  Reviewing {filename}...")

        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": (
                    f"Review this Python file for bugs, style issues, and security vulnerabilities. "
                    f"For each issue found, respond with one line in this exact format:\n"
                    f"LINE <n> [<severity>]: <description>\n\n"
                    f"Severity must be one of: critical, high, medium, low.\n"
                    f"If no issues, write: no issues found.\n\n"
                    f"=== {filename} ===\n{content}"
                ),
            }],
        )

        raw = next(
            (block.text for block in response.content if block.type == "text"), ""
        )

        # Parse: LINE 3 [critical]: SQL injection
        issues: list[dict] = []
        for line in raw.splitlines():
            match = re.match(
                r"LINE\s+(\d+)\s+\[(\w+)\]:\s+(.+)", line.strip(), re.IGNORECASE
            )
            if match:
                issues.append({
                    "line":        int(match.group(1)),
                    "severity":    match.group(2).lower(),
                    "description": match.group(3).strip(),
                })

        results[filename] = issues

    return results


# ----- Cross-File Integration Pass -----
  
def cross_file_pass(
    codebase: dict[str, str],
    per_file_results: dict[str, list[dict]],
) -> str:
    """
    Takes per-file summaries + file structure and checks for cross-cutting concerns:
    - Inconsistent API usage across files
    - Data flow issues between modules
    - Same pattern handled differently in different files
    """
    # Build a compact summary of per-file findings
    summary = "\n".join(
        f"{filename}: {len(issues)} issues — "
        + ("; ".join(i["description"] for i in issues) if issues else "no issues")
        for filename, issues in per_file_results.items()
    )

    # Build a simple import/dependency graph from source
    import_graph: dict[str, list[str]] = {}
    for filename, content in codebase.items():
        imports = re.findall(r"^(?:import|from)\s+([\w.]+)", content, re.MULTILINE)
        import_graph[filename] = imports

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": (
                "You are doing a cross-file integration review. "
                "Based on the per-file summaries and import graph below, identify:\n"
                "1. Data flow issues between modules\n"
                "2. Inconsistent API usage across files\n"
                "3. Same pattern handled differently in different files\n"
                "4. Security issues that span multiple files\n\n"
                f"Per-file summaries:\n{summary}\n\n"
                f"Import graph:\n{import_graph}\n\n"
                "List each cross-file issue clearly, referencing the specific files involved."
            ),
        }],
    )

    return next(
        (block.text for block in response.content if block.type == "text"), ""
    )

# ----- Smoke Test -----

if __name__ == "__main__":
    sample_dir = Path(__file__).parent / "sample_code"
    codebase = load_codebase(str(sample_dir))

    # Single-pass
    # print("\n" + "="*60)
    # print("SINGLE-PASS REVIEW")
    # print("="*60)
    # single_raw = single_pass_review(codebase)
    # print(single_raw)

    # Per-file
    print("\n" + "="*60)
    print("PER-FILE REVIEW")
    print("="*60)
    per_file_results = per_file_review(codebase)
    for filename, issues in per_file_results.items():
        print(f"  {filename}: {len(issues)} issues found")
        for issue in issues:
            print(f"    line {issue['line']} [{issue['severity']}]: {issue['description']}")

    # Cross-file
    print("\n" + "="*60)
    print("CROSS-FILE INTEGRATION PASS")
    print("="*60)
    cross_file_result = cross_file_pass(codebase, per_file_results)
    print(cross_file_result)


