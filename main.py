#!/usr/bin/env python3
"""
Wallet Recovery Tool - Main Entry Point
=======================================
Production-ready wallet recovery and database integration system

Quick Start:
    python main.py extract <dataset_path>    - Extract crypto keys from dataset  
    python main.py scan                      - Scan database keys for balances
    python main.py monitor                   - Start continuous monitoring
    python main.py analyze                   - Analyze all results
    python main.py setup                     - Setup database and environment
"""

import sys
import os
from pathlib import Path

# Add src directories to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path / 'core'))
sys.path.insert(0, str(src_path / 'scanners'))
sys.path.insert(0, str(src_path / 'extractors'))
sys.path.insert(0, str(src_path / 'utils'))
sys.path.insert(0, str(src_path / 'reports'))

# Import the main tool
from wallet_tool import main

if __name__ == "__main__":
    main()
