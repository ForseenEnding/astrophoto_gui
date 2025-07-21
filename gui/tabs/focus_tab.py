from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QFormLayout, QSpinBox
)
from PySide6.QtCore import Qt, Signal

class FocusTab(QWidget):
    """Focus assistance tab"""
    
    # Signals
    start_focus_clicked = Signal()
    stop_focus_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the focus tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Focus controls
        self.start_focus_btn = QPushButton("Start Focus")
        self.start_focus_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #ffffff;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #666666;
            }
        """)
        self.start_focus_btn.clicked.connect(self.start_focus_clicked.emit)
        self.start_focus_btn.setEnabled(False)
        layout.addWidget(self.start_focus_btn)
        
        self.stop_focus_btn = QPushButton("Stop Focus")
        self.stop_focus_btn.setStyleSheet("""
            QPushButton {
                background-color: #660000;
                border: 1px solid #880000;
                border-radius: 4px;
                color: #ffffff;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #770000;
            }
            QPushButton:pressed {
                background-color: #550000;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #666666;
            }
        """)
        self.stop_focus_btn.clicked.connect(self.stop_focus_clicked.emit)
        self.stop_focus_btn.setEnabled(False)
        layout.addWidget(self.stop_focus_btn)
        
        # Focus settings
        focus_group = QGroupBox("Focus Settings")
        focus_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ffffff;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        focus_layout = QFormLayout(focus_group)
        focus_layout.setSpacing(5)
        
        self.focus_region_spinbox = QSpinBox()
        self.focus_region_spinbox.setRange(50, 500)
        self.focus_region_spinbox.setValue(200)
        self.focus_region_spinbox.setSuffix(" px")
        self.focus_region_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px;
                min-width: 60px;
                font-size: 10px;
            }
        """)
        focus_layout.addRow("Region:", self.focus_region_spinbox)
        
        layout.addWidget(focus_group)
        layout.addStretch()
        
    def update_camera_status(self, connected: bool):
        """Update button states based on camera connection"""
        self.start_focus_btn.setEnabled(connected)
        self.stop_focus_btn.setEnabled(False)  # Only enabled when focus is active
        
    def get_focus_settings(self) -> dict:
        """Get current focus settings"""
        return {
            "region_size": self.focus_region_spinbox.value()
        }
        
    def set_focus_active(self, active: bool):
        """Update UI state when focus is active"""
        self.start_focus_btn.setEnabled(not active)
        self.stop_focus_btn.setEnabled(active) 