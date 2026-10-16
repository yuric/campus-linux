#!/usr/bin/env python3
"""Measure the three real Tauri debs; refuse any unreviewed fixture package layout."""
import argparse
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("adapter", Path(__file__).with_name("install-deb.py"))
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--architecture", required=True, choices=["arm64", "amd64"])
parser.add_argument("packages", nargs=3, type=Path)
args = parser.parse_args()
records = [adapter.package_record(adapter.read_limited(path.resolve(), adapter.ABSOLUTE_PACKAGE_LIMIT)) for path in args.packages]
value = adapter.validate_admission({"schema": 1, "package": adapter.PACKAGE,
    "architecture": args.architecture, "max_package_bytes": max(record["size"] for record in records),
    "max_expanded_data_bytes": max(record["expanded_data_bytes"] for record in records),
    "packages": sorted(records, key=lambda record: record["version"])})
args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
print(json.dumps({"admission_sha256": adapter.digest(args.output.read_bytes()),
    "max_package_bytes": value["max_package_bytes"], "max_expanded_data_bytes": value["max_expanded_data_bytes"],
    "packages": [{key: record[key] for key in ("version", "architecture", "size", "sha256")} for record in value["packages"]]}, sort_keys=True))
