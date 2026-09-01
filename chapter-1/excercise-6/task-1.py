import math
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

def compare_results(
    codebase: dict[str, str],
    single_raw: str,
    per_file_results: dict[str, list[dict]],
) -> None:
    """
    Compare single-pass vs per-file pass:
    - Issue counts per file
    - Consistency (std deviation)
    - Drop-off pattern in single-pass
    """

    # Count issue mentions per file in single-pass raw text
    single_counts: dict[str, int] = {}
    for filename in codebase:
        # count how many "Line N" references appear under each file section
        pattern = rf"##\s*{re.escape(filename)}(.*?)(?=##|\Z)"
        section = re.search(pattern, single_raw, re.DOTALL | re.IGNORECASE)
        if section:
            single_counts[filename] = len(re.findall(r"line\s+\d+", section.group(1), re.IGNORECASE))
        else:
            single_counts[filename] = 0

    multi_counts = {f: len(issues) for f, issues in per_file_results.items()}

    def std_dev(values: list[int]) -> float:
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))

    print(f"{'FILE':<25} {'SINGLE-PASS':>12} {'PER-FILE':>10}")
    print("-" * 50)
    for filename in codebase:
        sp = single_counts.get(filename, 0)
        mp = multi_counts.get(filename, 0)
        flag = " ⚠️ " if mp > sp else ""
        print(f"  {filename:<23} {sp:>12} {mp:>10}{flag}")

    print("-" * 50)
    sp_vals = list(single_counts.values())
    mp_vals = list(multi_counts.values())
    print(f"  {'TOTAL':<23} {sum(sp_vals):>12} {sum(mp_vals):>10}")
    print(f"  {'STD DEV':<23} {std_dev(sp_vals):>12.2f} {std_dev(mp_vals):>10.2f}")
    print()
    print("Lower std dev = more consistent analysis across files.")
    print("Higher total in per-file = fewer issues missed due to attention dilution.")

# ----- Smoke Test -----

if __name__ == "__main__":
      sample_dir = Path(__file__).parent / "sample_code"
      codebase = load_codebase(str(sample_dir))
  
      # Single-pass
      print("\n" + "="*60)
      print("SINGLE-PASS REVIEW")
      print("="*60)
      single_raw = single_pass_review(codebase)
      print(single_raw)
  
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
  
      # Comparison
      print("\n" + "="*60)
      print("COMPARISON: SINGLE-PASS vs MULTI-PASS")
      print("="*60)
      compare_results(codebase, single_raw, per_file_results)



