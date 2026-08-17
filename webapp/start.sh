#!/bin/bash
# Launch reAlIty Web — FastAPI server
# Opens http://localhost:8000 in your browser automatically

echo "Starting reAlIty Web server..."
echo "(First run will load the AI model — this may take 30-60 seconds)"
echo ""

# Try to open browser (cross-platform)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8000 &
elif command -v open &> /dev/null; then
    open http://localhost:8000 &
fi

# Run server
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000 --reload
