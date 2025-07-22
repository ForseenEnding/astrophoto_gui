from pathlib import Path


from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout
)

# Import our GUI components
from gui.widgets.preview_widget import PreviewWidget
from gui.control_panel import TabbedControlPanel

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main window UI"""
        self.setWindowTitle("Astrophotography Camera")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set minimum size
        self.setMinimumSize(800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create preview widget (takes most of the space)
        self.preview_widget = PreviewWidget()
        main_layout.addWidget(self.preview_widget, stretch=4)
        
        # Create control menu (fixed width)
        self.control_menu = TabbedControlPanel()
        main_layout.addWidget(self.control_menu)
        
        # Apply global stylesheet
        self.apply_stylesheet()
        
    def apply_stylesheet(self):
        """Apply the global CSS stylesheet"""
        stylesheet_path = Path("styles.css")
        if stylesheet_path.exists():
            with open(stylesheet_path, "r") as f:
                self.setStyleSheet(f.read())
        else:
            # Fallback to basic dark theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1a1a1a;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #1a1a1a;
                    color: #ffffff;
                }
            """)
        