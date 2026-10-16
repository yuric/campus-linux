#!/usr/bin/env python3
"""Validate bootstrap evidence structure, never treat planned tests as runtime passes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_JOBS = {"verify_amd64", "verify_arm64"}


def resolve_pointer(document, pointer):
    if not isinstance(pointer, str) or not pointer.startswith("#/"):
        raise ValueError("invalid schema pointer")
    node = document
    try:
        for part in pointer[2:].split("/"):
            if re.search(r"~(?![01])", part):
                raise ValueError("invalid JSON pointer escape")
            key = part.replace("~1", "/").replace("~0", "~")
            if isinstance(node, list):
                if not re.fullmatch(r"0|[1-9][0-9]*", key):
                    raise ValueError("invalid JSON pointer array index")
                node = node[int(key)]
            else:
                node = node[key]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"dangling schema pointer: {pointer}") from exc
    return node


def check_contract_bindings(data, source, spec_bytes):
    if data.get("server_contract_source") != source.strip():
        raise ValueError("ledger contract source mismatch")
    if data.get("server_contract_sha256") != hashlib.sha256(spec_bytes).hexdigest():
        raise ValueError("ledger contract hash mismatch")
    # Receipt-only admission does not parse the spec or require PyYAML.
    import yaml
    spec = yaml.safe_load(spec_bytes)
    operations = pointers = 0
    for row in data["actions"]:
        for op in row["operations"]:
            path, method = op.get("path"), op.get("method")
            if not isinstance(path, str) or not isinstance(method, str):
                raise ValueError("missing operation path/method")
            expected = "#/paths/" + path.replace("~", "~0").replace("/", "~1") + "/" + method.lower()
            if op.get("schema_pointer") != expected:
                raise ValueError("operation pointer/path/method mismatch")
            operation = resolve_pointer(spec, expected)
            if (not isinstance(operation, dict) or not op.get("operation_id")
                    or operation.get("operationId") != op["operation_id"]):
                raise ValueError("wrong or missing operationId")
            pointers += 1
            for pointer in op["schema_refs"]:
                resolve_pointer(spec, pointer)
                pointers += 1
            operations += 1
    return operations, pointers


def check_inventory(root=ROOT):
    data = json.loads((root / "docs/acceptance/actions.json").read_text())
    operations, pointers = check_contract_bindings(
        data, (root / "contract/.source").read_text(),
        (root / "contract/api/docs/openapi.yaml").read_bytes())
    print(f"Contract ledger: {operations} operation mappings; {pointers} resolved pointers")
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
    check_control_audit(root, data)
    protocol = json.loads((root / "docs/acceptance/visual-protocol.json").read_text())
    if protocol["p95_frame_ms_max"] != 33.3 or protocol["duration_seconds"] != 60:
        raise ValueError("premeasurement gate changed; requires explicit criteria review")
    if sum(x["duration_seconds"] for x in protocol["sequence"]) != 60:
        raise ValueError("sequence does not cover 60 seconds")
    print(f"Inventory: {len(ids)} explicit unimplemented action cases; no product passes")


def check_control_audit(root, data):
    """Require an inspectable disposition, not an inferred semantic pass from row counts."""
    census = json.loads((root / "docs/acceptance/mac-control-census.json").read_text())
    audit = json.loads((root / "docs/acceptance/control-reconciliation.json").read_text())
    if audit.get("mac_sha") != data["mac_sha"] or census["mac_sha"] != data["mac_sha"]:
        raise ValueError("control audit/source pin mismatch")
    cases = {row["test_case"]: row for row in data["actions"]}
    expected = {(file["path"], line) for file in census["files"] for line in file["control_lines"]}
    seen = set()
    for entry in audit["entries"]:
        if entry.get("disposition") not in {"case", "duplicate", "local", "platform"}:
            raise ValueError("control audit requires an explicit disposition")
        if not entry.get("trace") or not entry.get("cases"):
            raise ValueError("control audit requires trace and acceptance cases")
        if any(case not in cases for case in entry["cases"]):
            raise ValueError("control audit references an unknown acceptance case")
        for line in entry["lines"]:
            location = (entry["path"], line)
            if location in seen or location not in expected:
                raise ValueError("duplicate or non-census control disposition")
            seen.add(location)
    if seen != expected:
        raise ValueError("undispositioned census control")
    for row in cases.values():
        if row["provenance_kind"] == "mac-observed-control":
            if not row.get("source_trace") or row.get("execution_kind") not in {"local", "request"}:
                raise ValueError(f"{row['test_case']}: observed control needs a traced execution kind")
            if bool(row["operations"]) != (row["execution_kind"] == "request"):
                raise ValueError(f"{row['test_case']}: local/request mapping contradicts trace")
        if any(case not in cases for case in row.get("related_cases", [])):
            raise ValueError("unknown related acceptance case")
    print(f"Control audit: {len(seen)} census locations dispositioned; semantic review still required")


def check_receipts(directory, head, results, source_root=ROOT):
    if set(results) != REQUIRED_JOBS or any(value != "success" for value in results.values()):
        raise ValueError("required architecture job missing/skipped/cancelled/failed")
    if not re.fullmatch(r"[a-f0-9]{40}", head):
        raise ValueError("invalid exact head")
    actual_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_root, text=True, timeout=30).strip()
    if actual_head != head:
        raise ValueError("admission checkout does not match expected head")
    archive_hash = hashlib.sha256(subprocess.check_output(
        ["git", "archive", head], cwd=source_root, timeout=60)).hexdigest()
    for arch in ["amd64", "arm64"]:
        receipt = json.loads((directory / f"receipt-{arch}.json").read_text())
        lock = json.loads((source_root / "ci/toolchain-lock.json").read_text())
        if (receipt.get("version") != 1 or receipt.get("head") != head or receipt.get("arch") != arch
                or receipt.get("repository") != "yuric/campus-linux"
                or receipt.get("result") != "success" or receipt.get("scope") != "repository-policy"
                or receipt.get("product_runtime") != "not-run" or receipt.get("desktop") != "not-run"
                or receipt.get("base") != lock["verification_base"]):
            raise ValueError(f"{arch}: mismatched receipt")
        for key in ["image_id"]:
            if not re.fullmatch(r"sha256:[a-f0-9]{64}", receipt.get(key, "")):
                raise ValueError(f"{arch}: missing image identity")
        if receipt.get("dockerfile_sha256") != hashlib.sha256((source_root / "ci/Dockerfile.verify").read_bytes()).hexdigest():
            raise ValueError("receipt used different Dockerfile")
        digest = receipt.get("archive_sha256", "")
        if not re.fullmatch(r"[a-f0-9]{64}", digest) or archive_hash != digest:
            raise ValueError("receipt source archive does not match expected commit")
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
