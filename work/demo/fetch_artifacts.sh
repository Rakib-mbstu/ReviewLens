#!/usr/bin/env bash
# Fetch the evaluation artifacts that are gitignored in this repo.
#
# runs/, cache/ and the mined corpus under data/ are not committed: the run
# outputs and cached responses are build products, and the corpus is 90 PRs of
# raw GitHub data that a pinned PR list plus a mining script records better than
# a git blob. That is the right call for the repository and the wrong one for a
# reader, who ends up with a pipeline that cannot replay anything. This script
# closes that gap.
#
#   bash work/demo/fetch_artifacts.sh          # fetch if missing
#   bash work/demo/fetch_artifacts.sh --check  # exit 0 if present, 1 if not
#
# Idempotent: it does nothing when the artifacts are already in place, and never
# overwrites them.
set -uo pipefail

TAG=v0.1.0
ASSET=reviewlens-artifacts-v0.1.0.tar.gz
URL="https://github.com/Rakib-mbstu/ReviewLens/releases/download/$TAG/$ASSET"
SHA256=6803efe5d3f8c4a6bb5f6289f66be55d1dae26fc30de85e5e090749e6ca85b26

# Three markers, one per directory, because a partial extraction is worse than
# no extraction: a missing corpus file surfaces as an empty denominator rather
# than an error.
present() {
  [ -f runs/subset30/claude-opus/run_meta.json ] &&
  [ -d cache ] && [ -n "$(ls -A cache 2>/dev/null)" ] &&
  [ -f data/corpus-subset30/mockito__mockito__2650.json ]
}

if [ "${1:-}" = "--check" ]; then present; exit $?; fi

if present; then
  echo "Artifacts already present — nothing to fetch."
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl not found. Download $URL by hand and extract it at the repo root." >&2
  exit 1
fi

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "Fetching $ASSET (~3MB) from the $TAG release…"
if ! curl -fsSL --retry 3 -o "$TMP/$ASSET" "$URL"; then
  cat >&2 <<MSG
ERROR: could not download $URL

  If you are offline, or the release has moved, the artifacts are not
  reconstructable from this clone alone: runs/ and cache/ are build products and
  data/ is mined from GitHub. To rebuild them from scratch you need a read-only
  GITHUB_TOKEN and an OPENROUTER_API_KEY, and the LLM calls are not free.
MSG
  exit 1
fi

# Verify before extracting: the bundle carries the numbers every report in this
# repo cites, so silently replaying a different one would be worse than failing.
if command -v shasum >/dev/null 2>&1; then
  GOT=$(shasum -a 256 "$TMP/$ASSET" | cut -d' ' -f1)
elif command -v sha256sum >/dev/null 2>&1; then
  GOT=$(sha256sum "$TMP/$ASSET" | cut -d' ' -f1)
else
  GOT=""
  echo "WARNING: no shasum/sha256sum available; skipping checksum verification." >&2
fi
if [ -n "$GOT" ] && [ "$GOT" != "$SHA256" ]; then
  echo "ERROR: checksum mismatch." >&2
  echo "  expected $SHA256" >&2
  echo "  got      $GOT" >&2
  exit 1
fi

tar xzf "$TMP/$ASSET"
echo "Extracted runs/, cache/ and data/. See runs/BUNDLE.txt for what is in them."
present || { echo "ERROR: extraction did not produce the expected layout." >&2; exit 1; }
