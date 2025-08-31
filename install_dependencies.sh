#!/bin/bash

# Fitbit Importer - Install System Dependencies
# Run this script with sudo to install required Python packages

echo "🚀 Installing Fitbit Importer Dependencies"
echo "=========================================="

# Update package list
echo "📦 Updating package list..."
apt update

# Install core Python data processing packages
echo "📊 Installing pandas and related packages..."
apt install -y python3-pandas python3-numpy python3-dateutil

# Install other useful packages that might be needed
echo "🔧 Installing additional Python packages..."
apt install -y python3-requests python3-click python3-configparser

# Install pip for packages not available via apt
echo "📦 Installing pip for additional packages..."
apt install -y python3-pip

# Install Fitbit API libraries via pip
echo "💓 Installing Fitbit API libraries..."
pip3 install --break-system-packages fitbit myfitbit

# Install dashboard and visualization libraries
echo "📊 Installing dashboard dependencies..."
pip3 install --break-system-packages streamlit plotly seaborn

# Install optional packages for better experience
echo "✨ Installing optional packages..."
apt install -y python3-dotenv || echo "dotenv not available in system packages (optional)"

echo ""
echo "✅ Installation complete!"
echo ""
echo "🧪 Testing pandas installation..."
python3 -c "import pandas; print('✅ Pandas version:', pandas.__version__)" 2>/dev/null || echo "❌ Pandas installation failed"

echo ""
echo "📋 Testing Fitbit Importer CLI..."
cd /home/tim/repos/fitbitImporter
python3 main.py --help

echo ""
echo "🧪 Testing dashboard dependencies..."
python3 -c "import streamlit; print('✅ Streamlit version:', streamlit.__version__)" 2>/dev/null || echo "❌ Streamlit installation failed"
python3 -c "import plotly; print('✅ Plotly version:', plotly.__version__)" 2>/dev/null || echo "❌ Plotly installation failed"

echo ""
echo "🎯 Ready to test commands!"
echo "Data processing: python3 main.py process-takeout"
echo "Health dashboard: streamlit run dashboard.py"