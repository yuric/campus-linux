#!/usr/bin/env bash
# The authority boundary as a failing build (PRD D7, ARCHITECTURE.md "Where the authority
# line sits"). Rails decides; this client renders. A provider, engine, model, stage, priority
# or credential-kind name may appear in client source only as a decoded field, never as a
# literal the client reasons about, and a failure's meaning never comes from matching its
# message.
#
# Scope: the client source directories listed in SOURCE_DIRS that exist. Until implementation
# starts none exist and the check passes vacuously.
#
# Exemption: a line that must carry a literal (a contract fixture, a snapshot test) ends with
# a comment `campus-boundary: allow <reason>`. The reason is required and is reviewed.
set -euo pipefail
cd "$(dirname "$0")/.."

SOURCE_DIRS=(src crates apps packages)
EXTENSIONS='\.(rs|ts|tsx|js|jsx)$'

# Vocabulary the API publishes. Kept short and literal on purpose; it mirrors the enums in
# docs/api/openapi.yaml (providers, engines, credential kinds, stages, priorities) and is
# extended only when the contract grows.
LITERALS='"(anthropic|openai|google|xai|openrouter|claude|codex|gemini|agy|grok|api_key|cli_subscription|ambient|imaginarium|seashore|in_progress|department|blocked|done|closed|P0|P1|P2|P3)"'
# Inferring meaning from a message or a status: the thing the Mac and web clients drifted on.
PATTERNS='(error|message|reason|detail)[A-Za-z_.]*\s*\.\s*(includes|contains|starts_with|startsWith|match|matches|indexOf)\s*\('

dirs=()
for d in "${SOURCE_DIRS[@]}"; do [ -d "$d" ] && dirs+=("$d"); done
if [ ${#dirs[@]} -eq 0 ]; then
  echo "check-client-boundary: no client source yet; nothing to check"
  exit 0
fi

fail=0
while IFS= read -r f; do
  while IFS= read -r line; do
    n=${line%%:*}; text=${line#*:}
    case "$text" in *"campus-boundary: allow "*) continue ;; esac
    echo "::error file=$f,line=$n::domain literal or error-substring match in client code: $text"
    fail=1
  done < <(grep -nE "$LITERALS|$PATTERNS" "$f" || true)
done < <(find "${dirs[@]}" -type f | grep -E "$EXTENSIONS" | grep -v node_modules | grep -v '/target/')

if [ $fail -ne 0 ]; then
  echo "A client renders what the API decides. Move the rule to campus-server or mark a fixture 'campus-boundary: allow <reason>'."
fi
exit $fail
