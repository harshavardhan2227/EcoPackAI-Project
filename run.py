"""
EcoPackAI – Local Development Launcher
Run:  python run.py
Open: http://localhost:5000
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
from app import app

if __name__ == '__main__':
    print("\n" + "="*52)
    print("  EcoPackAI - Local Server")
    print("  http://localhost:5000")
    print("  http://localhost:5000/dashboard")
    print("="*52 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
