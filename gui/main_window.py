import sys
import os
from pathlib import Path
from datetime import datetime, timezone

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction

# Import our core components
from core.camera.camera_controller import camera_controller, CameraStatus
from core.camera.camera_settings import SettingProfile

# Import our GUI components
from gui.preview_widget import PreviewWidget
from gui.control_panel import TabbedControlPanel

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        self.setup_timers()
        
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
        self.control_menu.panel_toggled.connect(self.on_control_panel_toggled)
        main_layout.addWidget(self.control_menu)
        
        # Apply global stylesheet
        self.apply_stylesheet()
        
    def setup_connections(self):
        """Setup signal connections"""
        # Connect camera controller signals
        camera_controller.camera_status_changed.connect(self.on_camera_status_changed)
        camera_controller.preview_image_captured.connect(self.on_preview_image_captured)
        camera_controller.image_captured.connect(self.on_image_captured)
        
        # Connect control panel signals
        self.control_menu.connect_clicked.connect(self.connect_camera)
        self.control_menu.disconnect_clicked.connect(self.disconnect_camera)
        self.control_menu.preview_clicked.connect(self.toggle_preview)
        self.control_menu.panel_toggled.connect(self.on_control_panel_toggled)

        
        # Connect camera settings signals
        camera_controller.settings_changed.connect(self.on_settings_changed)
        
    def setup_timers(self):
        """Setup timers for periodic updates"""
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.capture_preview)
        self.preview_active = False
        self.preview_framerate = 1  # Default 1 FPS
        
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
            
    def connect_camera(self):
        """Connect to the camera"""
        try:
            camera_controller.connect()
        except Exception as e:
            print(f"Failed to connect to camera: {e}")
            
    def disconnect_camera(self):
        """Disconnect from the camera"""
        try:
            self.stop_preview()
            camera_controller.disconnect()
        except Exception as e:
            print(f"Failed to disconnect from camera: {e}")
            
    def capture_image(self):
        """Capture a single image"""
        try:
            # Create data directory if it doesn't exist
            data_dir = Path("data/captures")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}"
            
            image_path = camera_controller.capture_image(data_dir / filename)
            print(f"Image captured: {image_path}")
            
        except Exception as e:
            print(f"Failed to capture image: {e}")
            
    def toggle_preview(self):
        """Toggle live preview on/off"""
        if self.preview_active:
            self.stop_preview()
        else:
            self.start_preview()
            
    def start_preview(self):
        """Start live preview"""
        self.preview_active = True
        interval = int(1000 / self.preview_framerate)  # Convert FPS to milliseconds
        self.preview_timer.start(interval)
        
    def update_preview_framerate(self, fps: int):
        """Update the preview framerate"""
        self.preview_framerate = max(1, min(30, fps))  # Clamp between 1-30 FPS
        if self.preview_active:
            # Restart timer with new interval
            interval = int(1000 / self.preview_framerate)
            self.preview_timer.start(interval)
        
    def stop_preview(self):
        """Stop live preview"""
        self.preview_active = False
        self.preview_timer.stop()
        
    def capture_preview(self):
        """Capture a preview image"""
        try:
            if camera_controller.get_status() == CameraStatus.CONNECTED:
                image_data = camera_controller.capture_preview()
                self.preview_widget.set_image(image_data=image_data)
        except Exception as e:
            print(f"Failed to capture preview: {e}")
            
    def on_camera_status_changed(self, event):
        """Handle camera status changes"""
        self.control_menu.update_camera_status(event.status)
        
    def on_preview_image_captured(self, event):
        """Handle preview image captured events"""
        print(f"Preview image captured, data type: {type(event.image_data)}, size: {len(event.image_data) if hasattr(event.image_data, '__len__') else 'unknown'}")
        self.preview_widget.set_image(image_data=event.image_data)
        
    def on_image_captured(self, event):
        """Handle image captured events"""
        if not event.image_paths:
            print("No images captured")
            return
            
        # Update session statistics
        self.control_menu.increment_image_count()
        
        # Select the best file for preview (prioritize JPG over CR2/RAW)
        preview_file = self._get_preview_file(event.image_paths)
        if preview_file:
            print(f"Using {preview_file} for preview")
            self.preview_widget.set_image(image_path=preview_file)
        else:
            print("No suitable preview file found")
            
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
            
        # Priority order: JPG > JPEG > other formats
        preview_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif']
        
        # First, try to find a JPG/JPEG file
        for ext in preview_extensions:
            for file_path in saved_files:
                if Path(file_path).suffix.lower() == ext:
                    return str(file_path)
        
        # If no preview-friendly format found, return the first file
        # (this will be CR2/RAW if that's all we have)
        return str(saved_files[0])

    def on_control_panel_toggled(self, expanded: bool):
        """Handle the control panel's expanded/collapsed signal"""
        # The panel handles its own expansion/collapse
        # This method can be used for any additional logic when panel state changes
        pass
        
    def on_settings_changed(self, event):
        """Handle camera settings changed events"""
        print(f"Camera settings changed: {event.settings}") 