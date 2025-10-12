#!/usr/bin/env python3
"""
Google Minesweeper Solver - Main Entry Point

A hardcoded minesweeper solver specifically designed for Google Minesweeper.
Uses precise pixel coordinates and dimensions for board detection and game control.
Optimized for Google Chrome at 110% zoom.
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gui import UniversalMinesweeperGUI

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('minesweeper_solver.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_dependencies():
    """Check if all required dependencies are available."""
    try:
        import configparser
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install configparser")
        return False

def verify_structure():
    """Verify that the required directory structure exists."""
    required_dirs = ['src', 'assets', 'temp']
    required_files = ['config.ini']
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"Missing directory: {dir_name}")
            return False
    
    for file_name in required_files:
        if not os.path.exists(file_name):
            print(f"Missing file: {file_name}")
            return False
    
    return True

def main():
    """Main entry point for the minesweeper solver."""
    print("Google Minesweeper Solver v3.0")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Verify structure
    if not verify_structure():
        print("Please ensure all required files and directories are present.")
        sys.exit(1)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Minesweeper Solver")
    
    try:
        # Create and run GUI
        gui = UniversalMinesweeperGUI()
        
        # Run the GUI (this will block until closed)
        gui.run()
        
        logger.info("Application closed")
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        logger.info("Application interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
