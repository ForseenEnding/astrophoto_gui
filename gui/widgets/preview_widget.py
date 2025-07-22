import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QImage
from core.analysis.analysis_manager import analysis_manager
from core.camera.preview_manager import preview_manager
from core.camera.camera_manager import camera_manager, PreviewImageCapturedEvent
import logging

logger = logging.getLogger(__name__)

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
        camera_manager.preview_image_captured.connect(self.on_preview_image_captured)
        
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
            success = image.loadFromData(image_data)
            
            if success and not image.isNull():
                pixmap = QPixmap.fromImage(image)
            else:
                logger.debug("Failed to load image from data")
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
        zoomed_size = available_size * preview_manager.get_zoom() / 100.0
        
        if preview_manager.get_aspect_ratio():
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
        preview_manager.set_aspect_ratio(keep)
        self.update_display()
        
    def set_zoom_factor(self, zoom: float):
        """Set the zoom factor for the image"""
        preview_manager.set_zoom(zoom)
        self.update_display() 

    def set_analysis_enabled(self, enabled: bool):
        analysis_manager.analyze_previews(enabled)
        self.update_display()

    def start_preview(self, framerate=None):
        """Start live preview"""
        preview_manager.set_live_preview_active(True)
        if framerate is not None:
            preview_manager.set_framerate(framerate)

    def stop_preview(self):
        """Stop live preview"""
        preview_manager.set_live_preview_active(False)

    def update_preview_framerate(self, fps: int):
        """Update the preview framerate"""
        preview_manager.set_framerate(fps)

    def capture_preview(self):
        """Capture a preview image (to be filled in after moving logic)"""
        pass

    def on_preview_image_captured(self, event: PreviewImageCapturedEvent):
        """Handle preview image captured events"""
        logger.debug(f"Preview image captured, data type: {type(event.image_data)}, size: {len(event.image_data) if hasattr(event.image_data, '__len__') else 'unknown'}")
        self.set_image(image_data=event.image_data)

    def on_image_captured(self, event, session_tab=None):
        """Handle image captured events. Optionally update session statistics via session_tab."""
        if not event.image_paths:
            logger.debug("No images captured")
            return
        if session_tab:
            session_tab.increment_image_count()
        preview_file = self._get_preview_file(event.image_paths)
        if preview_file:
            logger.debug(f"Using {preview_file} for preview")
            self.set_image(image_path=preview_file)
        else:
            logger.debug("No suitable preview file found")

    def _get_preview_file(self, saved_files: list) -> str:
        """
        Determine which file should be used for preview.
        Prioritizes JPG over CR2/RAW files for better compatibility.
        Args:
            saved_files: List of saved file paths (strings)
        Returns:
            Path to the file to use for preview, or None if no suitable file found
        """
        if not saved_files:
            return None
        preview_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif']
        for ext in preview_extensions:
            for file_path in saved_files:
                if Path(file_path).suffix.lower() == ext:
                    return str(file_path)
        return str(saved_files[0]) if saved_files else None 