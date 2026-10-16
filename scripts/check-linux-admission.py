#!/usr/bin/env python3
"""Coordinator's read-only gate; skipped GitHub checks are never successful evidence."""
import argparse
import json
import subprocess

REQUIRED = {
    "Internal links resolve", "OpenAPI spec parses", "Client renders, API decides",
    "Linux policy x86_64", "Linux policy arm64", "Linux verification admission",
}


def validate(pr, repository, expected_head):
    if repository.get("visibility") != "PUBLIC":
        raise ValueError("visibility blocker: public hosted eligibility required; coordinator owns settings")
    if pr.get("headRefOid") != expected_head:
        raise ValueError("PR head changed; obtain new exact-head evidence")
    checks = pr.get("statusCheckRollup") or []
    for name in REQUIRED:
        found = [c for c in checks if c.get("name", c.get("context")) == name]
        if not found or any(c.get("status") != "COMPLETED" or c.get("conclusion") != "SUCCESS" for c in found):
            raise ValueError(f"required check absent, pending, skipped or failed: {name}")


def gh(*args):
    return json.loads(subprocess.check_output(["gh", *args], text=True, timeout=60))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pr", required=True)
    p.add_argument("--head", required=True)
    args = p.parse_args()
    pr = gh("pr", "view", args.pr, "--repo", "yuric/campus-linux", "--json", "headRefOid,statusCheckRollup")
    repo = gh("repo", "view", "yuric/campus-linux", "--json", "visibility")
    validate(pr, repo, args.head)
    print("PASS current PR head and all required checks; coordinator still owns review/Council/merge")


if __name__ == "__main__":
    main()
