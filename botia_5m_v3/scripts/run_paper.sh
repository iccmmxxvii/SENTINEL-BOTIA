#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs data
python3 -m venv .venv
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -e .
python -m botia5m doctor
python -m botia5m run --paper
