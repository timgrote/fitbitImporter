#!/bin/bash

# Fitbit Importer - Dependency Installation Script for Ubuntu/Debian
# This script installs all required dependencies for building the application with Fyne GUI

set -e  # Exit on error

echo "========================================="
echo "Fitbit Importer - Installing Dependencies"
echo "========================================="
echo ""

# Check if running on Ubuntu/Debian
if ! command -v apt-get &> /dev/null; then
    echo "Error: This script is designed for Ubuntu/Debian systems with apt-get"
    echo "For other systems, please install the dependencies manually."
    exit 1
fi

# Check if running with sudo privileges
if [ "$EUID" -ne 0 ]; then 
    echo "This script needs to install system packages."
    echo "Please run with sudo: sudo bash install-dependencies.sh"
    exit 1
fi

echo "Updating package list..."
apt-get update

echo ""
echo "Installing build essentials and Go dependencies..."
apt-get install -y \
    build-essential \
    gcc \
    golang \
    pkg-config

echo ""
echo "Installing OpenGL and X11 development libraries for Fyne GUI..."
apt-get install -y \
    libgl1-mesa-dev \
    xorg-dev \
    libx11-dev \
    libxcursor-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxi-dev \
    libxxf86vm-dev \
    libx11-xcb-dev \
    libxkbcommon-dev \
    libxkbcommon-x11-dev

echo ""
echo "Installing additional libraries that may be needed..."
apt-get install -y \
    libglu1-mesa-dev \
    freeglut3-dev \
    mesa-common-dev

echo ""
echo "========================================="
echo "✓ All dependencies installed successfully!"
echo "========================================="
echo ""
echo "You can now build the application with:"
echo "  go build -o fitbit-importer cmd/main.go"
echo ""
echo "Or run it directly with:"
echo "  go run cmd/main.go"
echo ""