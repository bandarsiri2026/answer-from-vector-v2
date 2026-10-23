#!/usr/bin/env python3
"""Sanity checks for the sanitized n8n workflow exports.

Run:  python3 scripts/validate_workflows.py
Exit code 1 if a secret-like token or a dangling connection is found.
"""
import json
import pathlib
import re
import sys
from collections import Counter

WORKFLOW_DIR = pathlib.Path(__file__).resolve().parent.parent / "workflows"

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_]{10,}",                        # OpenAI keys
    r"AIza[A-Za-z0-9_-]{10,}",                      # Google API keys
    r"GOCSPX-[A-Za-z0-9_-]+",                       # OAuth client secrets
    r"ya4\.[A-Za-z0-9_]{20,}",                      # Google refresh tokens
    r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{5,}",    # JWTs
]
PLACEHOLDER = re.compile(
    r"<REPLACE_WITH_[A-Z_]+>|<APPLICANT_[A-Z]+>|<YOUR_EMAIL>|<FALLBACK_EMAIL>"
)


def main() -> int:
    failures = []
    for path in sorted(WORKFLOW_DIR.glob("*.json")):
        text = path.read_text(encoding="utf-8")
        doc = json.loads(text)

        node_names = {n["name"] for n in doc.get("nodes", [])}
        retries = sum(1 for n in doc["nodes"] if n.get("retryOnFail"))
        disabled = sum(1 for n in doc["nodes"] if n.get("disabled"))
        kinds = Counter(n["type"].split(".")[-1] for n in doc["nodes"])

        dangling = []
        for source, conns in doc.get("connections", {}).items():
            if source not in node_names:
                dangling.append("connection from missing node " + repr(source))
            branches = conns.get("main") or conns.get("output", {}).get("main") or []
            for branch in branches:
                for link in branch or []:
                    if link["node"] not in node_names:
                        dangling.append(source + " -> " + repr(link["node"]) + " is not present")

        secrets = [p for p in SECRET_PATTERNS if re.search(p, text)]
        placeholders = sorted(set(PLACEHOLDER.findall(text)))

        print(
            "{}: {} nodes | retries on {} nodes | disabled {} | kinds: {}".format(
                path.name, len(node_names), retries, disabled, ", ".join(sorted(kinds))
            )
        )
        print("   placeholders: " + (", ".join(placeholders) if placeholders else "none"))

        if secrets:
            failures.append(path.name + ": secret-like pattern found")
        if dangling:
            failures.append(path.name + ": " + "; ".join(dangling))

    if failures:
        print("\nFAILED:")
        for f in failures:
            print("  - " + f)
        return 1

    print("\nOK: workflows parse, contain no secret-like tokens and have valid connections.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
