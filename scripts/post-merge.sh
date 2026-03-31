#!/bin/bash
set -e

pip install -r requirements.txt --quiet --exists-action i

python scripts/update_seed.py || true
