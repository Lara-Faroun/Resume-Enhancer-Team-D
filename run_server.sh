#!/bin/bash
# Linux/Mac script to run the server with correct PYTHONPATH
cd "$(dirname "$0")"
export PYTHONPATH="$PWD"
python -m uvicorn app.main:app --reload
