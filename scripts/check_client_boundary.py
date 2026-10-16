#!/usr/bin/env python3
"""Bounded lexical checks for PRD D7. See docs/client-boundary.md for the contract."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re


EXTENSIONS = {".rs", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"}
IGNORED_DIRS = {".git", ".gstack", ".claude", ".venv", "node_modules", "target", "dist", "build"}
VOCABULARY = set("""
anthropic openai google xai openrouter claude codex gemini agy grok
api_key cli_subscription ambient imaginarium seashore in_progress department
blocked done closed P0 P1 P2 P3
""".split())
MARKER = "campus-boundary: allow"
TOKENS = re.compile(
    r'(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)'
    r'|(?P<raw>\br(?P<hashes>\#*)"[\s\S]*?"(?P=hashes))'
    r'|(?P<string>"(?:\\[\s\S]|[^"\\])*"|\'(?:\\[^\n]|[^\'\\\n])*\'|`(?:\\[\s\S]|[^`\\])*`)'
)
ESCAPES = re.compile(r"\\(?:x([0-9a-fA-F]{2})|u([0-9a-fA-F]{4})|u\{([0-9a-fA-F]+)\})")
ERROR_MATCH = re.compile(
    r"\b(?:error|message|reason|detail)[\w.]*\s*(?:\?\.|\.)\s*"
    r"(?:includes|contains|starts_with|startsWith|match|matches|indexOf)\s*\("
)
TRANSITIONS = re.compile(
    r"\b(?:[a-z_]*transitions?|[a-z_]*transition_?table)\s*"
    r"(?::[^=;\n]+)?=\s*(?:&\s*)?(?:\{|\[|new\s+Map\b)", re.IGNORECASE
)


def is_fixture(path):
    return bool(
        {"test", "tests", "__tests__", "fixtures", "__fixtures__"}.intersection(path.parts)
        or re.search(r"\.(test|spec)\.[cm]?[jt]sx?$", path.name)
    )


def check_source(path, source):
    hits, allowed, masked = [], set(), []
    cursor = 0
    for token in TOKENS.finditer(source):
        text = token.group()
        line = source.count("\n", 0, token.start()) + 1
        if token.group("comment") is not None:
            for offset, comment_line in enumerate(text.splitlines()):
                if MARKER not in comment_line:
                    continue
                reason = comment_line.split(MARKER, 1)[1].removesuffix("*/").strip()
                if not is_fixture(path) or not reason:
                    hits.append((line + offset, "allow comments require a fixture path and a nonempty reason"))
                else:
                    allowed.add(line + offset)
        else:
            if token.group("raw") is not None:
                count = len(token.group("hashes"))
                value = text[count + 2:len(text) - count - 1]
            else:
                value = ESCAPES.sub(
                    lambda match: chr(int(next(group for group in match.groups() if group), 16)),
                    text[1:-1],
                )
            if value in VOCABULARY:
                hits.append((line, "domain literal requires API data or a reviewed boundary exception"))
        masked.append(source[cursor:token.start()])
        masked.append(re.sub(r"[^\n]", " ", text))
        cursor = token.end()
    masked.append(source[cursor:])
    code = "".join(masked)
    for pattern, message in (
        (ERROR_MATCH, "error-substring interpretation belongs in Rails"),
        (TRANSITIONS, "workflow-transition table belongs in Rails"),
    ):
        for match in pattern.finditer(code):
            hits.append((code.count("\n", 0, match.start()) + 1, message))
    return sorted(set((line, message) for line, message in hits if line not in allowed))


def source_files(root):
    def fail_walk(error):
        raise error

    files = {}
    for directory, dirs, names in os.walk(root, onerror=fail_walk):
        dirs[:] = sorted(name for name in dirs if name not in IGNORED_DIRS)
        for name in dirs:
            if (Path(directory) / name).is_symlink():
                raise ValueError("source directory symlinks are not supported")
        for name in sorted(names):
            path = Path(directory) / name
            if path.suffix in EXTENSIONS:
                if path.is_symlink():
                    raise ValueError("source file symlinks are not supported")
                files[path.relative_to(root).as_posix()] = path
    return files


def reviewed_files(root, files):
    policy = json.loads((root / "scripts/client-boundary-policy.json").read_text())
    if not isinstance(policy, dict) or policy.get("version") != 1:
        raise ValueError("unsupported boundary policy version")
    entries = policy.get("reviewed_files")
    if not isinstance(entries, list):
        raise ValueError("reviewed_files must be a list")
    reviewed = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("invalid reviewed file entry")
        name = entry["path"]
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or name not in files or name in reviewed:
            raise ValueError("reviewed paths must be unique existing source files inside the repository")
        if entry.get("kind") not in {"generated-contract", "executor-adapter"}:
            raise ValueError("reviewed file kind must be generated-contract or executor-adapter")
        if any(not isinstance(entry.get(key), str) or not entry[key].strip() for key in ("reason", "evidence")):
            raise ValueError("reviewed files require a nonempty reason and evidence")
        if entry.get("sha256") != hashlib.sha256(files[name].read_bytes()).hexdigest():
            raise ValueError("reviewed file content changed; renew its review and SHA-256 receipt")
        reviewed.add(name)
    return reviewed


def check(root):
    try:
        files = source_files(root)
        reviewed = reviewed_files(root, files)
        findings = [
            (name, line, message)
            for name, path in files.items() if name not in reviewed
            for line, message in check_source(PurePosixPath(name), path.read_text())
        ]
    except (OSError, ValueError, TypeError) as error:
        print(f"check-client-boundary: cannot verify policy: {error}")
        return 1
    for name, line, message in findings:
        # Do not echo source lines: a diagnostic must not expose credentials or payloads.
        print(f"{name}:{line}: {message}")
    if not files:
        print("No product source yet; policy-tooling tests are separate from app verification.")
    else:
        print(f"Checked {len(files)} source files ({len(reviewed)} reviewed exceptions); {len(findings)} findings.")
    return int(bool(findings))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    raise SystemExit(check(parser.parse_args().root.resolve()))
