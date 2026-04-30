#!/usr/bin/env bash
set -e

WORKSPACE_DIR="$1"

echo "Setup core in: $WORKSPACE_DIR"

mkdir -p "$WORKSPACE_DIR/shared/opencode"
mkdir -p "$WORKSPACE_DIR/shared/logs"

echo "Core setup completato"
