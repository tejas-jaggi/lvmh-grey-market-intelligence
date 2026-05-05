#!/usr/bin/env python3
"""
setup.py — One-click setup for LVMH Grey Market Prototype Phase 1
Run: python setup.py
"""

import subprocess
import sys
import os


def run(cmd, desc=""):
    print(f"\n[run] {desc or cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=False)
    if result.returncode != 0:
        print(f"  [fail] {cmd}")
        sys.exit(1)
    return result


def main():
    print("\n" + "=" * 55)
    print("  LVMH Grey Market Intelligence - Phase 1 Setup")
    print("  IS 534 | Group 1 | UIUC")
    print("=" * 55)

    # Check Python version
    major, minor = sys.version_info[:2]
    print(f"\n[ok] Python {major}.{minor} detected")
    if major < 3 or minor < 9:
        print("  [warn] Python 3.9+ recommended")

    # Install dependencies
    run(
        f"{sys.executable} -m pip install -r requirements.txt --quiet",
        "Installing Python dependencies..."
    )
    print("  [ok] Dependencies installed")

    # Seed DB by importing and running
    print("\n[run] Seeding database with synthetic LVMH data...")
    os.environ["FLASK_APP"] = "app.py"
    
    # Import and seed
    sys.path.insert(0, os.getcwd())
    from app import app, initialize_db
    with app.app_context():
        from database import db
        from data_generator import seed_all
        db.create_all()
        seed_all()

    print("\n" + "=" * 55)
    print("  [ok] Setup complete!")
    print("\n  To start the prototype:")
    print("     python app.py")
    print("\n  Then open in browser:")
    print("     http://localhost:5000")
    print("\n  Phase 1 pages:")
    print("     http://localhost:5000          -> Dashboard")
    print("     http://localhost:5000/listings -> Marketplace Monitor")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
