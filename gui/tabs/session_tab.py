from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QFormLayout, QLineEdit, QSpinBox, QMessageBox, QComboBox,
    QProgressBar, QTextEdit, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, Signal
from core.session.sessions import SessionState, session_manager, Session
from core.camera.camera_settings import SettingProfile
from core.equipment.equipment import equipment_manager, Telescope, Camera
from core.camera.camera_controller import camera_controller, CameraStatus
from gui.widgets.setting_profile_box import SettingProfileBox, ProfileMode
from gui.widgets.session_dialog import SessionDialog
import logging
import time

logger = logging.getLogger(__name__)


class CaptureSequenceWorker(QThread):
    """Worker thread for handling capture sequence"""
    progress_updated = Signal(int, int)  # current, total
    capture_completed = Signal(str)  # file path
    sequence_completed = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, session: Session, save_directory: Path):
        super().__init__()
        self.session = session
        self.save_directory = save_directory
        self._stop_requested = False
        
    def run(self):
        """Run the capture sequence"""
        try:
            # Ensure camera is connected
            if camera_controller.get_status() != CameraStatus.CONNECTED:
                camera_controller.connect()
            
            # Apply session settings to camera
            if self.session.settings:
                settings_dict = self.session.settings.as_dict()["settings"]
                camera_controller.set_settings(settings_dict)
                logger.info(f"Applied settings: {settings_dict}")
            
            # Create session directory
            session_dir = self.save_directory / f"{self.session.target}_{self.session.created_at.strftime('%Y%m%d_%H%M%S')}"
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Capture sequence
            for i in range(self.session.exposures):
                if self._stop_requested:
                    logger.info("Capture sequence stopped by user")
                    break
                
                # Generate filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{self.session.target}_{timestamp}_{i+1:04d}"
                save_path = session_dir / filename
                
                # Capture image
                try:
                    captured_files = camera_controller.capture_image(save_path)
                    if captured_files:
                        self.capture_completed.emit(str(captured_files[0]))
                        logger.info(f"Captured exposure {i+1}/{self.session.exposures}: {captured_files[0]}")
                    else:
                        logger.warning(f"No files captured for exposure {i+1}")
                        
                except Exception as e:
                    logger.error(f"Error capturing exposure {i+1}: {e}")
                    self.error_occurred.emit(f"Capture error: {e}")
                    break
                
                # Update progress
                self.progress_updated.emit(i + 1, self.session.exposures)
                
                # Small delay between captures
                time.sleep(0.5)
            
            if not self._stop_requested:
                self.sequence_completed.emit()
                
        except Exception as e:
            logger.error(f"Sequence error: {e}")
            self.error_occurred.emit(f"Sequence error: {e}")
    
    def stop(self):
        """Request stop of the sequence"""
        self._stop_requested = True


class SessionTab(QWidget):
    """Session management tab with sequence control"""    
    def __init__(self):
        super().__init__()
        self._current_session = None
        self._capture_worker = None
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # Session management box
        self.create_session_management_box()
        
        # Settings profile box
        self.create_settings_profile_box()
        
        # Sequence control box
        self.create_sequence_control_box()
        
        # Initialize with current session
        self.update_session_info()
        self.update_session_list()
        
    def setup_connections(self):
        """Setup signal connections"""
        # Session manager connections
        session_manager.current_session_changed.connect(self.on_session_manager_session_changed)
        
        # Camera controller connections
        camera_controller.camera_status_changed.connect(self.on_camera_status_changed)
        camera_controller.image_captured.connect(self.on_image_captured)
        
    def create_session_management_box(self):
        """Create the session management box"""
        session_box = QGroupBox("Session Management")
        session_layout = QVBoxLayout(session_box)
        
        # Session selection row
        selection_row = QHBoxLayout()
        selection_row.addWidget(QLabel("Active Session:"))
        
        self.session_list = QComboBox()
        self.session_list.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px;
                min-width: 200px;
                font-size: 10px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
        """)
        self.session_list.currentIndexChanged.connect(self.on_session_selected)
        selection_row.addWidget(self.session_list)
        
        # Modify session button
        self.modify_session_btn = QPushButton("Modify")
        self.modify_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                border: 1px solid #0088ee;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #0077dd;
            }
            QPushButton:pressed {
                background-color: #0055bb;
            }
        """)
        self.modify_session_btn.clicked.connect(self.modify_session)
        selection_row.addWidget(self.modify_session_btn)
        
        selection_row.addStretch()
        session_layout.addLayout(selection_row)
        
        # Session information
        info_layout = QFormLayout()
        info_layout.setAlignment(Qt.AlignTop)
        
        self.session_state_label = QLabel(text="No session selected")
        self.session_state_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        info_layout.addRow("State:", self.session_state_label)
        
        self.session_telescope_label = QLabel(text="No session selected")
        self.session_telescope_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        info_layout.addRow("Telescope:", self.session_telescope_label)
        
        self.session_camera_label = QLabel(text="No session selected")
        self.session_camera_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        info_layout.addRow("Camera:", self.session_camera_label)
        
        self.session_exposures_label = QLabel(text="No session selected")
        self.session_exposures_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        info_layout.addRow("Exposures:", self.session_exposures_label)
        
        self.session_created_at_label = QLabel(text="No session selected")
        self.session_created_at_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        info_layout.addRow("Created at:", self.session_created_at_label)
        
        self.session_updated_at_label = QLabel(text="No session selected")
        self.session_updated_at_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        info_layout.addRow("Updated at:", self.session_updated_at_label)
        
        session_layout.addLayout(info_layout)
        
        self.layout.addWidget(session_box)
        
    def create_settings_profile_box(self):
        """Create the settings profile box"""
        # Create setting profile box with edit mode
        self.settings_profile_box = SettingProfileBox(mode=ProfileMode.EDIT)
        self.settings_profile_box.setting_profile_changed.connect(self.on_settings_profile_changed)
        
        self.layout.addWidget(self.settings_profile_box)
        
    def create_sequence_control_box(self):
        """Create the sequence control box"""
        sequence_box = QGroupBox("Capture Sequence Control")
        sequence_layout = QVBoxLayout(sequence_box)
        
        # Camera status
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Camera Status:"))
        
        self.camera_status_label = QLabel("Disconnected")
        self.camera_status_label.setStyleSheet("color: #ff6666; font-size: 10px; font-weight: bold;")
        status_row.addWidget(self.camera_status_label)
        
        # Connect/Disconnect button
        self.camera_connect_btn = QPushButton("Connect")
        self.camera_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                border: 1px solid #0088ee;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #0077dd;
            }
            QPushButton:pressed {
                background-color: #0055bb;
            }
        """)
        self.camera_connect_btn.clicked.connect(self.toggle_camera_connection)
        status_row.addWidget(self.camera_connect_btn)
        
        status_row.addStretch()
        sequence_layout.addLayout(status_row)
        
        # Sequence controls
        controls_row = QHBoxLayout()
        
        self.start_sequence_btn = QPushButton("Start Sequence")
        self.start_sequence_btn.setStyleSheet("""
            QPushButton {
                background-color: #00aa00;
                border: 1px solid #00cc00;
                border-radius: 4px;
                color: #ffffff;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #00bb00;
            }
            QPushButton:pressed {
                background-color: #009900;
            }
            QPushButton:disabled {
                background-color: #555555;
                border-color: #666666;
                color: #888888;
            }
        """)
        self.start_sequence_btn.clicked.connect(self.start_sequence)
        controls_row.addWidget(self.start_sequence_btn)
        
        self.stop_sequence_btn = QPushButton("Stop Sequence")
        self.stop_sequence_btn.setStyleSheet("""
            QPushButton {
                background-color: #cc0000;
                border: 1px solid #ee0000;
                border-radius: 4px;
                color: #ffffff;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #dd0000;
            }
            QPushButton:pressed {
                background-color: #bb0000;
            }
            QPushButton:disabled {
                background-color: #555555;
                border-color: #666666;
                color: #888888;
            }
        """)
        self.stop_sequence_btn.clicked.connect(self.stop_sequence)
        self.stop_sequence_btn.setEnabled(False)
        controls_row.addWidget(self.stop_sequence_btn)
        
        controls_row.addStretch()
        sequence_layout.addLayout(controls_row)
        
        # Progress bar
        progress_row = QHBoxLayout()
        progress_row.addWidget(QLabel("Progress:"))
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 4px;
                text-align: center;
                background-color: #2a2a2a;
                color: #ffffff;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #0066cc;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_row.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("0/0")
        self.progress_label.setStyleSheet("color: #ffffff; font-size: 10px; min-width: 60px;")
        progress_row.addWidget(self.progress_label)
        
        sequence_layout.addLayout(progress_row)
        
        # Status display
        self.status_display = QTextEdit()
        self.status_display.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                font-family: monospace;
                font-size: 9px;
            }
        """)
        self.status_display.setMaximumHeight(100)
        self.status_display.setReadOnly(True)
        sequence_layout.addWidget(self.status_display)
        
        self.layout.addWidget(sequence_box)
        

        

        
    def update_session_info(self):
        """Update session information display"""
        if self._current_session:
            self.session_state_label.setText(self._current_session.state.value)
            
            # Display telescope information
            if self._current_session.telescope:
                telescope = self._current_session.telescope
                if telescope:
                    self.session_telescope_label.setText(f"{telescope.name} (f/{telescope.focal_ratio:.1f})")
                else:
                    self.session_telescope_label.setText(f"{self._current_session.telescope_name} (not found)")
            else:
                self.session_telescope_label.setText("No telescope selected")
            
            # Display camera information
            if self._current_session.camera:
                camera = self._current_session.camera
                if camera:
                    self.session_camera_label.setText(f"{camera.name} ({camera.pixel_width}x{camera.pixel_height})")
                else:
                    self.session_camera_label.setText(f"{self._current_session.camera_name} (not found)")
            else:
                self.session_camera_label.setText("No camera selected")
            
            # Display exposures count
            self.session_exposures_label.setText(str(self._current_session.exposures))
            
            self.session_created_at_label.setText(self._current_session.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            self.session_updated_at_label.setText(self._current_session.updated_at.strftime("%Y-%m-%d %H:%M:%S"))
            
            # Update settings profile box
            if self._current_session.settings:
                self.settings_profile_box.set_setting_profile(self._current_session.settings)
        else:
            self.session_state_label.setText("No session selected")
            self.session_telescope_label.setText("No session selected")
            self.session_camera_label.setText("No session selected")
            self.session_exposures_label.setText("No session selected")
            self.session_created_at_label.setText("No session selected")
            self.session_updated_at_label.setText("No session selected")
        
    def update_session_list(self):
        """Update the session selection combo box"""
        # Temporarily disconnect the signal to prevent triggering selection events
        self.session_list.currentIndexChanged.disconnect()
        
        self.session_list.clear()
        self.session_list.addItem("No session selected", None)
        
        for session in session_manager.get_all_sessions():
            self.session_list.addItem(f"{session.target} ({session.state.value})", session.id)
            if self._current_session and session.id == self._current_session.id:
                self.session_list.setCurrentText(f'{session.target} ({session.state.value})')
        
        # Reconnect the signal
        self.session_list.currentIndexChanged.connect(self.on_session_selected)
        
    def update_camera_status_display(self):
        """Update camera status display"""
        status = camera_controller.get_status()
        if status == CameraStatus.CONNECTED:
            self.camera_status_label.setText("Connected")
            self.camera_status_label.setStyleSheet("color: #00ff00; font-size: 10px; font-weight: bold;")
            self.camera_connect_btn.setText("Disconnect")
            self.start_sequence_btn.setEnabled(self._current_session is not None)
        elif status == CameraStatus.ERROR:
            self.camera_status_label.setText("Error")
            self.camera_status_label.setStyleSheet("color: #ff6666; font-size: 10px; font-weight: bold;")
            self.camera_connect_btn.setText("Connect")
            self.start_sequence_btn.setEnabled(False)
        else:
            self.camera_status_label.setText("Disconnected")
            self.camera_status_label.setStyleSheet("color: #ff6666; font-size: 10px; font-weight: bold;")
            self.camera_connect_btn.setText("Connect")
            self.start_sequence_btn.setEnabled(False)
                

        

        
    # Event handlers
    def on_session_selected(self, index):
        """Handle session selection"""
        if self.session_list.currentData():
            session_id = self.session_list.currentData()
            session_manager.set_current_session(session_id)
        else:
            session_manager.set_current_session(None)
            

            
    def on_settings_profile_changed(self, profile: SettingProfile):
        """Handle settings profile change"""
        if self._current_session:
            # Update the session's settings profile
            session_manager.update_session(self._current_session.id, settings=profile)
            
    def on_session_manager_session_changed(self, session: Optional[Session]):
        """Handle session manager session change"""
        self.set_current_session(session)
        
    def on_camera_status_changed(self, event):
        """Handle camera status change"""
        self.update_camera_status_display()
        self.log_status(f"Camera status: {event.status.value}")
        
    def on_image_captured(self, event):
        """Handle image captured event"""
        for image_path in event.image_paths:
            self.log_status(f"Image captured: {Path(image_path).name}")
        
    def toggle_camera_connection(self):
        """Toggle camera connection"""
        try:
            status = camera_controller.get_status()
            if status == CameraStatus.CONNECTED:
                camera_controller.disconnect()
                self.log_status("Camera disconnected")
            else:
                camera_controller.connect()
                self.log_status("Camera connected")
        except Exception as e:
            self.log_status(f"Camera connection error: {e}")
            QMessageBox.warning(self, "Connection Error", f"Failed to connect to camera: {e}")
        
    def start_sequence(self):
        """Start the capture sequence"""
        if not self._current_session:
            QMessageBox.warning(self, "No Session", "Please select a session first.")
            return
            
        if not self._current_session.settings:
            QMessageBox.warning(self, "No Settings", "Please configure camera settings for this session.")
            return
            
        # Create save directory
        save_directory = Path(self._current_session.folder / "captures")
        save_directory.mkdir(parents=True, exist_ok=True)
        
        # Create and start worker
        self._capture_worker = CaptureSequenceWorker(self._current_session, save_directory)
        self._capture_worker.progress_updated.connect(self.on_progress_updated)
        self._capture_worker.capture_completed.connect(self.on_capture_completed)
        self._capture_worker.sequence_completed.connect(self.on_sequence_completed)
        self._capture_worker.error_occurred.connect(self.on_sequence_error)
        
        # Update UI
        self.start_sequence_btn.setEnabled(False)
        self.stop_sequence_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(self._current_session.exposures)
        self.progress_label.setText(f"0/{self._current_session.exposures}")
        
        # Start sequence
        self._capture_worker.start()
        self.log_status(f"Started capture sequence: {self._current_session.exposures} exposures")
        
    def stop_sequence(self):
        """Stop the capture sequence"""
        if self._capture_worker and self._capture_worker.isRunning():
            self._capture_worker.stop()
            self.log_status("Stopping capture sequence...")
            
    def on_progress_updated(self, current: int, total: int):
        """Handle progress update"""
        percentage = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(f"{current}/{total}")
        
    def on_capture_completed(self, file_path: str):
        """Handle individual capture completion"""
        self.log_status(f"Captured: {Path(file_path).name}")
        
    def on_sequence_completed(self):
        """Handle sequence completion"""
        self.log_status("Capture sequence completed successfully!")
        self.reset_sequence_controls()
        
    def on_sequence_error(self, error: str):
        """Handle sequence error"""
        self.log_status(f"Sequence error: {error}")
        QMessageBox.critical(self, "Sequence Error", f"Capture sequence failed: {error}")
        self.reset_sequence_controls()
        
    def reset_sequence_controls(self):
        """Reset sequence control buttons"""
        self.start_sequence_btn.setEnabled(True)
        self.stop_sequence_btn.setEnabled(False)
        if self._capture_worker:
            self._capture_worker.wait()
            self._capture_worker = None
            
    def log_status(self, message: str):
        """Log status message to display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_display.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.status_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        

    
    def on_session_created(self, session: Session):
        """Handle session creation from dialog"""
        self.update_session_list()
        
        # Optionally select the newly created session
        session_manager.set_current_session(session.id)
        
    def on_session_deleted(self, session_id: str):
        """Handle session deletion from dialog"""
        self.update_session_list()
        
        # Clear current session if it was deleted
        if self._current_session and self._current_session.id == session_id:
            session_manager.set_current_session(None)
    
    def set_current_session(self, session: Optional[Session]):
        """Set the current session"""
        if session != self._current_session:  # Only log if actually changing
            logger.debug(f"Current session changed: {session}")
        self._current_session = session
        self.update_session_info()
        self.update_session_list()
        self.update_camera_status_display()
            
    def modify_session(self):
        """Open session management dialog"""
        dialog = SessionDialog(parent=self)
        dialog.session_created.connect(self.on_session_created)
        dialog.session_deleted.connect(self.on_session_deleted)
        dialog.exec()
        
    def closeEvent(self, event):
        """Clean up resources when widget is closed"""
        if self._capture_worker and self._capture_worker.isRunning():
            self._capture_worker.stop()
            self._capture_worker.wait()
        event.accept()
        
    def increment_image_count(self):
        """Increment the image count for statistics"""
        # This method can be used to track captured images
        # For now, just log the increment
        self.log_status("Image count incremented")
        
    def get_framerate(self) -> int:
        """Get the current framerate for preview"""
        # Default framerate, can be made configurable later
        return 1
        
    def add_exposure_time(self, exposure_seconds):
        """Add exposure time for statistics"""
        # This method can be used to track total exposure time
        # For now, just log the addition
        self.log_status(f"Added exposure time: {exposure_seconds} seconds")
        
