#!/usr/bin/env bash
# access_and_snapshot.sh — PART B ONLY
# Usage:
#   access_and_snapshot.sh <DATASET_PATH> [SAMPLE_N]
# Example:
#   access_and_snapshot.sh /path/to/yt_comments.csv.gz 1000
set -euo pipefail

DATASET="${1:-}"; N="${2:-1000}"
[ -n "$DATASET" ] || { echo "Usage: $(basename "$0") <DATASET_PATH> [SAMPLE_N]"; exit 2; }

# Resolve output dirs (snapshot area = parent of this script dir)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$OUT_ROOT/logs"
SAMPLES_DIR="$OUT_ROOT/data/samples"
mkdir -p "$LOG_DIR" "$SAMPLES_DIR"

# Pick streaming command
if [[ "$DATASET" == *.gz ]]; then
  STREAM="zcat \"$DATASET\""
elif [[ "$DATASET" == *.zip ]]; then
  STREAM="unzip -p \"$DATASET\""
else
  STREAM="cat \"$DATASET\""
fi

# 5-line peek (streamed)
eval "$STREAM" | head -5 | tee "$LOG_DIR/peek.txt" >/dev/null

# 1k sample preserving header; avoid multi-line rows by requiring a video_id at start
SAMPLE="$SAMPLES_DIR/sample_1k.csv"
if command -v shuf >/dev/null 2>&1; then
  { eval "$STREAM" | head -1; \
    eval "$STREAM" | tail -n +2 \
      | grep -E '^[A-Za-z0-9_-]{11},' \
      | shuf -n "$N"; } > "$SAMPLE"
else
  { eval "$STREAM" | head -1; \
    eval "$STREAM" | tail -n +2 \
      | grep -E '^[A-Za-z0-9_-]{11},' \
      | awk -v s="$N" '{buf[++n]=$0} END{
          if(n<s)s=n; srand();
          for(i=1;i<=s;i++){ j=int(rand()*n)+1; print buf[j]; buf[j]=buf[n--] }
        }'; } > "$SAMPLE"
fi

chmod a+r "$LOG_DIR/peek.txt" "$SAMPLE"
echo "Wrote:"
echo "  $LOG_DIR/peek.txt"
echo "  $SAMPLES_DIR/sample_1k.csv"
