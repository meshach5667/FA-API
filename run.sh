#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install or upgrade dependencies
pip install -r requirements.txt

# Run the FastAPI application
uvicorn app.main:app --reload
