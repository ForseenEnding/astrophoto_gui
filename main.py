#!/usr/bin/env python3
"""
Astrophotography Camera Application
Main entry point for the application
"""

import sys
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 