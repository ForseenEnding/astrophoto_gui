import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QSizePolicy, QScrollArea, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage

class PreviewWidget(QWidget):
    """Widget for displaying camera preview or captured images"""
    
    # Signals
    aspect_ratio_changed = Signal(bool)
    framerate_changed = Signal(int)
    zoom_changed = Signal(float)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_image = None
        self.keep_aspect_ratio = True
        self.zoom_factor = 1.0
        
    def setup_ui(self):
        """Setup the preview widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area for large images
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px solid #333333;
                border-radius: 8px;
                color: #cccccc;
            }
        """)
        
        # Set placeholder text
        self.image_label.setText("No Image Available")
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
    def set_image(self, image_data: bytes = None, image_path: str = None):
        """Set the image to display from bytes or file path"""
        pixmap = None
        
        if image_data:
            # Create QImage from bytes
            image = QImage()
            if isinstance(image_data, (bytes, bytearray)):
                success = image.loadFromData(image_data)
            else:
                # Convert to bytes if needed
                try:
                    image_data_bytes = bytes(image_data)
                    success = image.loadFromData(image_data_bytes)
                except Exception as e:
                    print(f"Failed to convert image data to bytes: {e}")
                    success = False
            
            if success and not image.isNull():
                pixmap = QPixmap.fromImage(image)
            else:
                print("Failed to load image from data")
                self.image_label.setText("Failed to load image from data")
                return
                
        elif image_path and os.path.exists(image_path):
            # Load from file
            pixmap = QPixmap(image_path)
        
        if pixmap and not pixmap.isNull():
            self.current_image = pixmap
            self.update_display()
        else:
            self.image_label.setText("Failed to load image")
            
    def update_display(self):
        """Update the displayed image with proper scaling"""
        if not self.current_image:
            return
            
        # Get available size
        available_size = self.scroll_area.size()
        
        # Apply zoom factor to available size
        zoomed_size = available_size * self.zoom_factor
        
        if self.keep_aspect_ratio:
            # Scale maintaining aspect ratio
            scaled_pixmap = self.current_image.scaled(
                zoomed_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            # Scale to fit exactly
            scaled_pixmap = self.current_image.scaled(
                zoomed_size,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            
        self.image_label.setPixmap(scaled_pixmap)
        
    def resizeEvent(self, event):
        """Handle resize events to update image scaling"""
        super().resizeEvent(event)
        self.update_display()
        
    def set_keep_aspect_ratio(self, keep: bool):
        """Set whether to keep aspect ratio when scaling"""
        self.keep_aspect_ratio = keep
        self.update_display()
        
    def set_zoom_factor(self, zoom: float):
        """Set the zoom factor for the image"""
        self.zoom_factor = zoom / 100.0
        self.update_display() 