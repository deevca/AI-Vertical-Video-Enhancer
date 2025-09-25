#!/bin/bash
# Setup script for AI Video Enhancer

echo "🚀 Setting up AI Video Enhancer..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔑 Creating .env file..."
    echo "# Replicate API Key for Stable Diffusion" > .env
    echo "# Get your key from: https://replicate.com/account/api-tokens" >> .env
    echo "REPLICATE_API_TOKEN=your_api_key_here" >> .env
    echo "✅ Please edit .env file and add your API key"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your Replicate API key"
echo "2. Run: ./run.py"
echo "3. Open: http://localhost:5001"
echo ""
