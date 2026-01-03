#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

export DJANGO_SETTINGS_MODULE="playground_server.settings"
python3 manage.py test blocks.tests
