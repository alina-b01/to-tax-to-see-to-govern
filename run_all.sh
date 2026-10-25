#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/analysis"
python descriptives.py
python regional.py
python municipal.py all
python reporting.py
python figures.py
