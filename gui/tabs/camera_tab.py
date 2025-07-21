from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QFormLayout, QMessageBox
)
from PySide6.QtCore import Signal, QTimer
from core.camera.camera_controller import CameraStatus, camera_controller
from gui.widgets.setting_profile_box import SettingProfileBox, ProfileMode
from pathlib import Path
from datetime import datetime
import logging

class CameraTab(QWidget):
    """Camera connection and info tab"""
    
    # Signals
    connect_clicked = Signal()
    disconnect_clicked = Signal()
    preview_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.preview_active = False
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.capture_preview)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the camera tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Camera status
        self.status_label = QLabel("Camera: Disconnected")
        self.status_label.setStyleSheet("color: #ff6666; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Camera buttons
        button_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setStyleSheet("""
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
        """)
        self.connect_btn.clicked.connect(self.connect_clicked.emit)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setStyleSheet("""
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
        """)
        self.disconnect_btn.clicked.connect(self.disconnect_clicked.emit)
        self.disconnect_btn.setEnabled(False)
        
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.disconnect_btn)
        layout.addLayout(button_layout)
        
        # Capture and preview buttons
        button_row = QHBoxLayout()
        
        self.capture_btn = QPushButton("Capture")
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #006600;
                border: 1px solid #008800;
                border-radius: 4px;
                color: #ffffff;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #007700;
            }
            QPushButton:pressed {
                background-color: #005500;
            }
            QPushButton:disabled {
                background-color: #444444;
                border-color: #555555;
                color: #888888;
            }
        """)
        self.capture_btn.clicked.connect(self.capture_image)
        self.capture_btn.setEnabled(False)
        button_row.addWidget(self.capture_btn)
        
        self.preview_btn = QPushButton("Live Preview")
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                border: 1px solid #0088ff;
                border-radius: 4px;
                color: #ffffff;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0077dd;
            }
            QPushButton:pressed {
                background-color: #0055bb;
            }
            QPushButton:disabled {
                background-color: #444444;
                border-color: #555555;
                color: #888888;
            }
        """)
        self.preview_btn.clicked.connect(self.toggle_preview)
        self.preview_btn.setEnabled(False)
        button_row.addWidget(self.preview_btn)
        
        layout.addLayout(button_row)
        
        # Camera info section
        info_group = QGroupBox("Camera Info")
        info_group.setStyleSheet("""
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
        
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(5)
        
        self.camera_model_label = QLabel("Not connected")
        self.camera_model_label.setStyleSheet("color: #cccccc; font-size: 10px;")
        info_layout.addRow("Model:", self.camera_model_label)
        
        self.camera_serial_label = QLabel("Not connected")
        self.camera_serial_label.setStyleSheet("color: #cccccc; font-size: 10px;")
        info_layout.addRow("Serial:", self.camera_serial_label)
        
        layout.addWidget(info_group)
        
        # Setting profile box (SELECT mode for camera tab)
        self.setting_profile_box = SettingProfileBox(mode=ProfileMode.EDIT)
        layout.addWidget(self.setting_profile_box)
        layout.addStretch()
        
    def update_camera_status(self, status: CameraStatus):
        """Update the camera status display"""
        if status == CameraStatus.CONNECTED:
            self.status_label.setText("Camera: Connected")
            self.status_label.setStyleSheet("color: #66ff66; font-weight: bold; font-size: 12px;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.capture_btn.setEnabled(True)
            self.preview_btn.setEnabled(True)
        elif status == CameraStatus.DISCONNECTED:
            self.status_label.setText("Camera: Disconnected")
            self.status_label.setStyleSheet("color: #ff6666; font-weight: bold; font-size: 12px;")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.capture_btn.setEnabled(False)
            self.preview_btn.setEnabled(False)
            # Stop preview if camera disconnects
            self.stop_preview()
        else:  # ERROR
            self.status_label.setText("Camera: Error")
            self.status_label.setStyleSheet("color: #ffaa00; font-weight: bold; font-size: 12px;")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.capture_btn.setEnabled(False)
            self.preview_btn.setEnabled(False)
            # Stop preview if camera has error
            self.stop_preview()
            
    def update_camera_info(self, model: str = None, serial: str = None):
        """Update camera information display"""
        if model:
            self.camera_model_label.setText(model)
        if serial:
            self.camera_serial_label.setText(serial)
            
    def capture_image(self):
        """Capture an image with the current settings profile"""
        try:
            # Check if camera is connected
            if camera_controller.get_status() != CameraStatus.CONNECTED:
                QMessageBox.warning(self, "Camera Not Connected", "Please connect to a camera first.")
                return
                
            # Get the current settings profile
            current_profile = self.setting_profile_box.setting_profile
            if not current_profile:
                QMessageBox.warning(self, "No Profile Selected", "Please select a settings profile first.")
                return
                
            # Apply the settings profile
            if not current_profile.apply():
                QMessageBox.critical(self, "Settings Error", "Failed to apply camera settings.")
                return
                
            # Create captures directory if it doesn't exist
            captures_dir = Path("./data/captures")
            captures_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}"
            
            # Capture the image
            captured_files = camera_controller.capture_image(captures_dir / filename)
            
            if captured_files:
                logging.info(f"Image captured: {captured_files}")
            else:
                logging.warning("No image was captured.")
                
        except Exception as e:
            logging.error(f"Error capturing image: {e}")
            QMessageBox.critical(self, "Capture Error", f"Failed to capture image: {e}")
            
    def toggle_preview(self):
        """Toggle live preview on/off"""
        if self.preview_active:
            self.stop_preview()
        else:
            self.start_preview()
            
    def start_preview(self):
        """Start live preview at 10 FPS"""
        try:
            if camera_controller.get_status() != CameraStatus.CONNECTED:
                QMessageBox.warning(self, "Camera Not Connected", "Please connect to a camera first.")
                return
                
            # Get the current settings profile
            current_profile = self.setting_profile_box.setting_profile
            if not current_profile:
                QMessageBox.warning(self, "No Profile Selected", "Please select a settings profile first.")
                return
                
            # Apply the settings profile
            if not current_profile.apply():
                QMessageBox.critical(self, "Settings Error", "Failed to apply camera settings.")
                return
                
            self.preview_active = True
            self.preview_btn.setText("Stop Preview")
            self.preview_btn.setStyleSheet("""
                QPushButton {
                    background-color: #cc0000;
                    border: 1px solid #ee0000;
                    border-radius: 4px;
                    color: #ffffff;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #dd0000;
                }
                QPushButton:pressed {
                    background-color: #bb0000;
                }
            """)
            
            # Start timer at 10 FPS (100ms interval)
            self.preview_timer.start(100)
            self.preview_clicked.emit()
            logging.info("Live preview started at 10 FPS")
            
        except Exception as e:
            logging.error(f"Error starting preview: {e}")
            QMessageBox.critical(self, "Preview Error", f"Failed to start preview: {e}")
            
    def stop_preview(self):
        """Stop live preview"""
        self.preview_active = False
        self.preview_timer.stop()
        self.preview_btn.setText("Live Preview")
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                border: 1px solid #0088ff;
                border-radius: 4px;
                color: #ffffff;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0077dd;
            }
            QPushButton:pressed {
                background-color: #0055bb;
            }
            QPushButton:disabled {
                background-color: #444444;
                border-color: #555555;
                color: #888888;
            }
        """)
        logging.info("Live preview stopped")
        
    def capture_preview(self):
        """Capture a preview image"""
        try:
            if camera_controller.get_status() == CameraStatus.CONNECTED:
                image_data = camera_controller.capture_preview()
                # Emit signal for main window to handle preview display
                # The main window will handle setting the image in the preview widget
                self.preview_clicked.emit()
                logging.debug("Preview image captured")
        except Exception as e:
            logging.error(f"Error capturing preview: {e}")
            # Stop preview on error
            self.stop_preview() 