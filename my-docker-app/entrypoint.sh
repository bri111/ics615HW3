#!/bin/bash
set -e

# Your main tasks here
echo "Running main tasks..."
# For example, run tests
pytest

# Keep the container running
tail -f /dev/null
