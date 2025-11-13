#!/bin/bash
echo "Installing dependencies..."
pip3 install flask 2>&1 | grep -v "already satisfied" || true
echo "Starting File Transfer App..."
python3 file_transfer_app.py
