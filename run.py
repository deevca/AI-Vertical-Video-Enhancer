#!/bin/bash
"""
Simple script to run the AI Video Enhancer
"""

echo "🚀 Starting AI Video Enhancer..."
echo "📱 Open your browser to: http://localhost:5001"
echo "🛑 Press Ctrl+C to stop"
echo

# Activate virtual environment and run the app
source venv/bin/activate
cd backend
python main.py
