#!/usr/bin/env bash
# Repository policy tooling only; this does not build or run the Linux app.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 scripts/check_client_boundary.py --root .
