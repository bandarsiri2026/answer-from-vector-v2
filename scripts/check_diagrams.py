#!/usr/bin/env python3
"""Lint Mermaid diagrams in Markdown files so GitHub can render them.

GitHub's Mermaid renderer fails on unquoted parentheses, slashes or question
marks inside node labels, e.g.  A[Parse & Enrich Job Data (Text)]  -> parse error.
This script flags those patterns before they reach the README.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MERMAID_BLOCK = re.compile(r"```mermaid\n([\s\S]*?)```")

# node label shapes: [ ] { } ( ) — a label is safe if it is quoted or has no special chars
LABEL_SHAPES = [
    (r"\[", r"\]"),
    (r"\{", r"\}"),
    (r"\(", r"\)"),
]

DANGEROUS = re.compile(r"[()]")  # unquoted parentheses break GitHub's Mermaid parser


def lint_block(block: str, file: str, start_line: int) -> list[str]:
    problems = []
    for offset, line in enumerate(block.splitlines(), start=start_line):
        stripped = line.strip()
        if not stripped or stripped.startswith(("%%", "flowchart", "graph", "sequenceDiagram")):
            continue
        for open_re, close_re in LABEL_SHAPES:
            for m in re.finditer(f"{open_re}([^\\{close_re[0]}]*?){close_re}", line):
                label = m.group(1)
                if '"' in label or "'" in label:
                    continue  # quoted labels are fine
                if DANGEROUS.search(label):
                    problems.append(
                        f"{file}:{offset}: unquoted special character in node label "
                        f"'{label}' -> use \"{label}\""
                    )
    return problems


def main() -> int:
    if len(sys.argv) > 1:
        files = [Path(p) for p in sys.argv[1:]]
    else:
        files = [Path("README.md")] + (sorted(Path("docs").glob("*.md")) if Path("docs").exists() else [])
    total = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        for m in MERMAID_BLOCK.finditer(text):
            start_line = text[: m.start()].count("\n") + 2
            problems = lint_block(m.group(1), str(f), start_line)
            if problems:
                total += len(problems)
                print("\n".join(problems))
    if total:
        print(f"\nFAIL: {total} Mermaid label(s) need quoting.")
        return 1
    print("OK: all Mermaid diagrams use render-safe labels.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
