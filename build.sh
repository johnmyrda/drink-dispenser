#!/usr/bin/env bash

set -x

# Lint
uv run ruff check
# Type Checking
uv run ty check
# Tests
uv run pytest
