# src/gui/__main__.py
"""
Entry point for running the GUI application as a module.
Usage: python -m src.gui.main_window
"""

import sys
from .main_window import main_gui

if __name__ == "__main__":
    sys.exit(main_gui())
