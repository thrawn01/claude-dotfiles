#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <target-directory>"
    echo "Example: $0 ~/.claude"
    exit 1
fi

TARGET_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Claude dotfiles to: $TARGET_DIR"

mkdir -p "$TARGET_DIR/commands"
mkdir -p "$TARGET_DIR/agents"

if [ -d "$SCRIPT_DIR/commands" ]; then
    echo "Copying commands..."
    for file in "$SCRIPT_DIR/commands/"*; do
        if [ "$(basename "$file")" != "README.md" ]; then
            cp -r "$file" "$TARGET_DIR/commands/"
        fi
    done
    echo "  $(find "$TARGET_DIR/commands" -maxdepth 1 -type f | wc -l) files copied to $TARGET_DIR/commands/"
else
    echo "Warning: commands/ directory not found"
fi

if [ -d "$SCRIPT_DIR/agents" ]; then
    echo "Copying agents..."
    for file in "$SCRIPT_DIR/agents/"*; do
        if [ "$(basename "$file")" != "README.md" ]; then
            cp -r "$file" "$TARGET_DIR/agents/"
        fi
    done
    echo "  $(find "$TARGET_DIR/agents" -maxdepth 1 -type f | wc -l) files copied to $TARGET_DIR/agents/"
else
    echo "Warning: agents/ directory not found"
fi

echo "Installation complete!"
