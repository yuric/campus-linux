#!/usr/bin/env python3
"""Real repository checks only. Future product seams must be added by their owners."""
import pathlib
import re
import subprocess

from check_contract import check

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMANDS = [
    ["python3", "-B", "-m", "unittest", "discover", "-s", "scripts/tests", "-v"],
    ["scripts/check-client-boundary.sh"],
    ["python3", "-B", "scripts/check_acceptance.py"],
]


def documents():
    for source in ROOT.rglob("*.md"):
        if any(part in {".git", "node_modules", "target", "build", "dist"} for part in source.parts):
            continue
        for link in re.findall(r"\]\(([^)]+)\)", source.read_text()):
            if link.startswith(("https://", "http://", "mailto:", "#")):
                continue
            target = link.split("#")[0]
            if target and not (source.parent / target).exists():
                raise ValueError(f"broken relative link: {source.relative_to(ROOT)} -> {target}")
    result = check(ROOT / "contract")
    print(f"Contract bundle verified: {result}")


def main():
    for command in COMMANDS:
        print("RUN " + " ".join(command), flush=True)
        subprocess.run(command, cwd=ROOT, check=True, timeout=180)
    documents()
    print("PASS repository policy/docs only; product runtime and desktop acceptance NOT RUN")


if __name__ == "__main__":
    main()
