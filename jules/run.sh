#!/usr/bin/env bash
set -euo pipefail

# simple Jules pipeline: install, smoke test, produce demo artifact
python -m pip install -r requirements.txt
pytest -q

python scripts/demo_colab_like.py
echo "Artifacts in ./out"
