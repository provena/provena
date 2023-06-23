#!/bin/bash

# Default port
port=8000

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --port)
            port="$2"
            shift
            shift
            ;;
        *)
            # Ignore unrecognized arguments
            shift
            ;;
    esac
done

# Start the server with the specified port
uvicorn main:app --reload --port "$port"