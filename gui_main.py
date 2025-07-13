#!/usr/bin/env python3
# gui_main.py - Entry point for GUI application build
"""
GUI application entry point for Nuitka build.
This file serves as the main entry point for building the GUI version of the application.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.gui.main_window import main_gui

if __name__ == "__main__":
    sys.exit(main_gui())
