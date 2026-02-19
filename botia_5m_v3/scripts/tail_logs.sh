#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
touch logs/botia5m.log
tail -f logs/botia5m.log
