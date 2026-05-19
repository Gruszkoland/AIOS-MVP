#!/usr/bin/env bash
set -e
echo "=== AIOS-MVP bootstrap ==="
rustc --version
cargo --version
python3 --version || true
echo "=== Done ==="
