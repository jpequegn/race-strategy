# GitHub Repository Setup Script
# Run this after cloning your new repository

#!/bin/bash

echo "🚀 Setting up DSPy Race Strategy Optimizer repository..."

# Create directory structure
mkdir -p src/{models,pipelines,data/{courses,athletes},utils}
mkdir -p tests/{unit,integration}
mkdir -p examples
mkdir -p docs
mkdir -p scripts

# Create __init__.py files for Python packages
touch src/__init__.py
touch src/models/__init__.py
touch src/pipelines/__init__.py
touch src/utils/__init__.py
touch tests/__init__.py

echo "📁 Directory structure created!"

# Set up Python virtual environment
python -m venv venv
echo "🐍 Virtual environment created!"

echo "✅ Repository structure ready!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate (or venv\\Scripts\\activate on Windows)"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Copy .env.example to .env and add your API keys"
echo "4. Run the demo: python examples/basic_demo.py"