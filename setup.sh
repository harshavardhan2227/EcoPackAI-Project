#!/bin/bash
# ============================================================
# EcoPackAI – Full Pipeline Setup Script
# Run this once to set up everything from scratch.
# Usage: bash setup.sh
# ============================================================

set -e  # Exit on any error

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║          🌿 EcoPackAI Setup Script            ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# 1. Install dependencies
echo "► Installing Python dependencies..."
pip install -r requirements.txt
echo "  ✔ Done"

# 2. Check data files
echo ""
echo "► Checking data files..."
if [ ! -f "data/materials_database_600.xlsx" ]; then
  echo "  ⚠  Missing: data/materials_database_600.xlsx"
  echo "     Please copy your Excel file to the data/ folder."
  exit 1
fi
if [ ! -f "data/real_packaging_history.xlsx" ]; then
  echo "  ⚠  Missing: data/real_packaging_history.xlsx"
  echo "     Please copy your Excel file to the data/ folder."
  exit 1
fi
echo "  ✔ Data files found"

# 3. Run pipeline
echo ""
echo "► Module 1: Data Collection & Management..."
python scripts/module1_data_collection.py

echo ""
echo "► Module 2: Feature Engineering..."
python scripts/module2_feature_engineering.py

echo ""
echo "► Module 3: ML Model Training..."
python scripts/module3_ml_training.py

echo ""
echo "► Module 7: BI Charts & Reports..."
python scripts/module7_bi_dashboard.py

# 4. Done
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║          ✅ Setup Complete!                   ║"
echo "║                                              ║"
echo "║  Launch:  python run.py                      ║"
echo "║  Open:    http://localhost:5000              ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
