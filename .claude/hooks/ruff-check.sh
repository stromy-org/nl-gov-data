#!/bin/bash
# PostToolUse hook: runs ruff check on Python files after Write/Edit
# Receives hook input JSON on stdin

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Skip non-Python files
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

# Skip if file doesn't exist (deleted)
if [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

# Run ruff check on the specific file
OUTPUT=$(uv run ruff check "$FILE_PATH" 2>&1)
EXIT_CODE=$?

if [[ $EXIT_CODE -ne 0 ]]; then
  echo "{\"decision\": \"block\", \"reason\": \"ruff check found issues in $FILE_PATH:\\n$OUTPUT\\nPlease fix these linting issues before continuing.\"}"
  exit 0
fi

exit 0
