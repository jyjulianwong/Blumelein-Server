#!/bin/bash

# Run the Blumelein Server API
# This script starts the FastAPI server with auto-reload enabled

echo "🌸 Starting Blumelein Server..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please copy .env.example to .env and configure your settings."
    echo ""
    echo "  cp .env.example .env"
    echo ""
    exit 1
fi

# Run the server with uvicorn
uv run uvicorn src.blumelein_server.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000


