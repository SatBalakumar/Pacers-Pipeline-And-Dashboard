#!/bin/bash

# Pacers Dashboard Launcher
# This script activates the conda environment and launches the Streamlit dashboard

echo "🏀 Starting Pacers Analytics Dashboard..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda not found"
    echo "Please install conda or miniconda first"
    exit 1
fi

# Initialize conda for bash (required for script activation)
eval "$(conda shell.bash hook)"

# Check if conda environment exists
if ! conda info --envs | grep -q "pacers_de"; then
    echo "❌ Error: pacers_de environment not found"
    echo "Please run: conda env create -f ../environment.yml"
    exit 1
fi

# Check if database exists
if [ ! -f "../db/pacers_analytics.db" ]; then
    echo "❌ Error: Database not found"
    echo "Please run: make build-all (from project root)"
    exit 1
fi

# Activate environment
echo "🔄 Activating conda environment 'pacers_de'..."
conda activate pacers_de

# Verify environment is active
if [[ "$CONDA_DEFAULT_ENV" != "pacers_de" ]]; then
    echo "❌ Error: Failed to activate pacers_de environment"
    echo "Current environment: $CONDA_DEFAULT_ENV"
    exit 1
fi

# Verify required packages
echo "🔍 Verifying required packages..."
python -c "import streamlit, pandas, plotly; print('✅ All packages available')" || {
    echo "❌ Error: Missing required packages"
    echo "Run: conda activate pacers_de && pip install streamlit plotly"
    exit 1
}

# Launch dashboard
echo "📊 Launching dashboard with conda environment..."
echo "🌐 Dashboard will open at: http://localhost:8502"
echo "🔄 Environment: $CONDA_DEFAULT_ENV"

streamlit run app.py