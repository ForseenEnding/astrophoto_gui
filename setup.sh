#!/bin/bash

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt