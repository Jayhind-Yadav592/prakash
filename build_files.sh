#!/bin/bash
# Determine available python binary
if command -v python3 &>/dev/null; then
    PY_BIN=python3
elif command -v python &>/dev/null; then
    PY_BIN=python
else
    echo "Python not found in PATH"
    exit 1
fi

echo "Using Python: $($PY_BIN --version)"
$PY_BIN -m pip install -r requirements.txt
$PY_BIN manage.py collectstatic --noinput
