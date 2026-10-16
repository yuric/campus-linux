#!/usr/bin/env python3
"""Validate bootstrap evidence structure, never treat planned tests as runtime passes."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_JOBS = {"verify_amd64", "verify_arm64"}


def check_inventory(root=ROOT):
    data = json.loads((root / "docs/acceptance/actions.json").read_text())
    ids = set()
    groups = set()
    for row in data["actions"]:
        case = row["test_case"]
        if case in ids:
            raise ValueError(f"duplicate test case {case}")
        ids.add(case)
        groups.add(row["group"])
        for field in ["action", "sources", "expected", "receipt", "contract_status"]:
            if not row.get(field):
                raise ValueError(f"{case}: missing {field}")
        if not 981 <= row["owner_card"] <= 999:
            raise ValueError(f"{case}: missing owning card")
        if row["status"] != "unimplemented":
            raise ValueError("bootstrap inventory cannot grant a product pass")
        for op in row["operations"]:
            if not op["schema_pointer"].startswith("#/paths/") or not op["method"] or not op["path"]:
                raise ValueError(f"{case}: incomplete operation/schema")
    if groups != {f"P{n:02}" for n in range(1, 19)}:
        raise ValueError("missing parity group")
    protocol = json.loads((root / "docs/acceptance/visual-protocol.json").read_text())
    if protocol["p95_frame_ms_max"] != 33.3 or protocol["duration_seconds"] != 60:
        raise ValueError("premeasurement gate changed; requires explicit criteria review")
    if sum(x["duration_seconds"] for x in protocol["sequence"]) != 60:
        raise ValueError("sequence does not cover 60 seconds")
    print(f"Inventory: {len(ids)} explicit unimplemented action cases; no product passes")


def check_receipts(directory, head, results):
    if set(results) != REQUIRED_JOBS or any(value != "success" for value in results.values()):
        raise ValueError("required architecture job missing/skipped/cancelled/failed")
    if not re.fullmatch(r"[a-f0-9]{40}", head):
        raise ValueError("invalid exact head")
    archive_hash = None
    for arch in ["amd64", "arm64"]:
        receipt = json.loads((directory / f"receipt-{arch}.json").read_text())
        lock = json.loads((ROOT / "ci/toolchain-lock.json").read_text())
        if (receipt.get("version") != 1 or receipt.get("head") != head or receipt.get("arch") != arch
                or receipt.get("repository") != "yuric/campus-linux"
                or receipt.get("result") != "success" or receipt.get("scope") != "repository-policy"
                or receipt.get("product_runtime") != "not-run" or receipt.get("desktop") != "not-run"
                or receipt.get("base") != lock["verification_base"]):
            raise ValueError(f"{arch}: mismatched receipt")
        for key in ["image_id"]:
            if not re.fullmatch(r"sha256:[a-f0-9]{64}", receipt.get(key, "")):
                raise ValueError(f"{arch}: missing image identity")
        if receipt.get("dockerfile_sha256") != hashlib.sha256((ROOT / "ci/Dockerfile.verify").read_bytes()).hexdigest():
            raise ValueError("receipt used different Dockerfile")
        digest = receipt.get("archive_sha256", "")
        if not re.fullmatch(r"[a-f0-9]{64}", digest) or archive_hash not in (None, digest):
            raise ValueError("architecture receipts used different source archives")
        archive_hash = digest
        if receipt.get("container_command") != "python3 -B scripts/verify_repository.py":
            raise ValueError("wrong verification command")
        for key in ["log", "packages"]:
            filename = receipt.get(key, "")
            if Path(filename).name != filename or not filename:
                raise ValueError("unsafe/missing artifact name")
            if hashlib.sha256((directory / filename).read_bytes()).hexdigest() != receipt.get(key + "_sha256"):
                raise ValueError("missing or modified receipt artifact")
    print("PASS exact-head architecture receipts; product/desktop evidence remains separate")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipts", type=Path)
    parser.add_argument("--head")
    parser.add_argument("--results", help="JSON map of required job results")
    args = parser.parse_args()
    if args.receipts:
        check_receipts(args.receipts, args.head, json.loads(args.results or "{}"))
    else:
        check_inventory()


if __name__ == "__main__":
    main()
