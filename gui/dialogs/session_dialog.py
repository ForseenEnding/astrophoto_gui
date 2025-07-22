from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QDialogButtonBox, QGroupBox, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QSplitter, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal
from core.session.sessions import Session, session_manager, SessionState
from core.camera.camera_settings import SettingProfile, default_profile
from core.equipment.equipment import equipment_manager
from gui.widgets.setting_profile_widget import SettingProfileBox, ProfileMode
from gui.dialogs.equipment_dialog import EquipmentDialog
import logging

logger = logging.getLogger(__name__)

class SessionDialog(QDialog):
    """Dialog for managing sessions - creating and deleting"""
    
    session_created = Signal(Session)  # Signal when a new session is created
    session_deleted = Signal(str)      # Signal when a session is deleted (session_id)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_sessions()
        self.load_equipment()
        
    def setup_ui(self):
        self.setWindowTitle("Session Management")
        self.setModal(True)
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Splitter for session list and creation form
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Session list
        list_group = QGroupBox("Existing Sessions")
        list_layout = QVBoxLayout(list_group)
        
        self.session_list = QListWidget()
        self.session_list.setStyleSheet("""
            QListWidget {
                background-color: #2a2a2a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                font-size: 10px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444444;
            }
            QListWidget::item:selected {
                background-color: #0066cc;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
        """)
        self.session_list.itemSelectionChanged.connect(self.on_session_selected)
        list_layout.addWidget(self.session_list)
        
        # Delete button
        self.delete_session_btn = QPushButton("Delete Session")
        self.delete_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #cc0000;
                border: 1px solid #ee0000;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #dd0000;
            }
            QPushButton:pressed {
                background-color: #bb0000;
            }
            QPushButton:disabled {
                background-color: #444444;
                border-color: #555555;
                color: #888888;
            }
        """)
        self.delete_session_btn.clicked.connect(self.delete_selected_session)
        self.delete_session_btn.setEnabled(False)
        list_layout.addWidget(self.delete_session_btn)
        
        splitter.addWidget(list_group)
        
        # Right side - Create new session
        create_group = QGroupBox("Create New Session")
        create_layout = QVBoxLayout(create_group)
        
        # Session information form
        form_layout = QFormLayout()
        
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Enter target name (e.g., M31, Orion Nebula)")
        self.target_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 10px;
            }
        """)
        form_layout.addRow("Target:", self.target_edit)
        
        # Equipment selection
        telescope_layout = QHBoxLayout()
        
        self.telescope_combo = QComboBox()
        self.telescope_combo.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
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
        self.telescope_combo.addItem("No telescope selected", "")
        telescope_layout.addWidget(self.telescope_combo)
        
        self.modify_telescope_btn = QPushButton("Modify")
        self.modify_telescope_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                border: 1px solid #0088ff;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #0077dd;
            }
        """)
        self.modify_telescope_btn.clicked.connect(self.modify_telescopes)
        telescope_layout.addWidget(self.modify_telescope_btn)
        
        form_layout.addRow("Telescope:", telescope_layout)
        
        camera_layout = QHBoxLayout()
        
        self.camera_combo = QComboBox()
        self.camera_combo.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
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
        self.camera_combo.addItem("No camera selected", "")
        camera_layout.addWidget(self.camera_combo)
        
        self.modify_camera_btn = QPushButton("Modify")
        self.modify_camera_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                border: 1px solid #0088ff;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #0077dd;
            }
        """)
        self.modify_camera_btn.clicked.connect(self.modify_cameras)
        camera_layout.addWidget(self.modify_camera_btn)
        
        form_layout.addRow("Camera:", camera_layout)
        
        # Exposure count
        self.exposures_spin = QSpinBox()
        self.exposures_spin.setRange(1, 1000)
        self.exposures_spin.setValue(10)
        self.exposures_spin.setStyleSheet("""
            QSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 10px;
            }
        """)
        form_layout.addRow("Exposures:", self.exposures_spin)
        
        create_layout.addLayout(form_layout)
        
        # Settings profile section
        settings_label = QLabel("Session Settings Profile:")
        settings_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 11px;")
        create_layout.addWidget(settings_label)
        
        self.settings_profile_box = SettingProfileBox(mode=ProfileMode.EDIT)
        self.settings_profile_box.set_setting_profile(default_profile)
        create_layout.addWidget(self.settings_profile_box)
        
        # Create button
        self.create_session_btn = QPushButton("Create Session")
        self.create_session_btn.setStyleSheet("""
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
        """)
        self.create_session_btn.clicked.connect(self.create_new_session)
        create_layout.addWidget(self.create_session_btn)
        
        splitter.addWidget(create_group)
        
        # Set splitter proportions
        splitter.setSizes([300, 400])
        
        layout.addWidget(splitter)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_sessions(self):
        """Load all sessions into the list"""
        self.session_list.clear()
        
        for session in session_manager.get_all_sessions():
            item = QListWidgetItem(f"{session.target} ({session.state.value})")
            item.setData(Qt.UserRole, session)
            self.session_list.addItem(item)
    
    def load_equipment(self):
        """Load equipment into combo boxes"""
        # Load telescopes
        self.telescope_combo.clear()
        self.telescope_combo.addItem("No telescope selected", "")
        
        for telescope in equipment_manager.get_all_telescopes():
            self.telescope_combo.addItem(f"{telescope.name} (f/{telescope.focal_ratio:.1f})", telescope.name)
        
        # Load cameras
        self.camera_combo.clear()
        self.camera_combo.addItem("No camera selected", "")
        
        for camera in equipment_manager.get_all_cameras():
            self.camera_combo.addItem(f"{camera.name} ({camera.pixel_width}x{camera.pixel_height})", camera.name)
            
    def on_session_selected(self):
        """Handle session selection in the list"""
        current_item = self.session_list.currentItem()
        self.delete_session_btn.setEnabled(current_item is not None)
        
    def create_new_session(self):
        """Create a new session"""
        target = self.target_edit.text().strip()
        if not target:
            QMessageBox.warning(self, "Invalid Target", "Please enter a target name.")
            return
            
        try:
            # Get the current settings profile
            settings = self.settings_profile_box.setting_profile
            
            # Get selected equipment
            telescope_name = self.telescope_combo.currentData()
            camera_name = self.camera_combo.currentData()
            
            # Get equipment objects
            telescope = equipment_manager.get_telescope(telescope_name) if telescope_name else None
            camera = equipment_manager.get_camera(camera_name) if camera_name else None
            
            # Get exposure count
            exposures = self.exposures_spin.value()
            
            # Create the session
            session = session_manager.create_session(target, settings, telescope, camera, exposures)
            
            self.log_status(f"Created session: {session.target}")
            self.load_sessions()
            
            # Clear the form
            self.target_edit.clear()
            self.settings_profile_box.set_setting_profile(default_profile)
            self.telescope_combo.setCurrentIndex(0)
            self.camera_combo.setCurrentIndex(0)
            
            # Emit signal
            self.session_created.emit(session)
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create session: {e}")
            
    def delete_selected_session(self):
        """Delete the selected session"""
        current_item = self.session_list.currentItem()
        if not current_item:
            return
            
        session = current_item.data(Qt.UserRole)
        if not session:
            return
            
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            f"Are you sure you want to delete the session '{session.target}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                session_id = session.id
                session_manager.remove_session(session_id)
                
                self.log_status(f"Deleted session: {session.target}")
                self.load_sessions()
                
                # Emit signal
                self.session_deleted.emit(session_id)
                
            except Exception as e:
                logger.error(f"Failed to delete session: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete session: {e}")
                
    def modify_telescopes(self):
        """Open equipment dialog to modify telescopes"""
        dialog = EquipmentDialog(self)
        dialog.equipment_updated.connect(self.load_equipment)
        dialog.exec()
        
    def modify_cameras(self):
        """Open equipment dialog to modify cameras"""
        dialog = EquipmentDialog(self)
        dialog.equipment_updated.connect(self.load_equipment)
        dialog.exec()
        
    def log_status(self, message: str):
        """Log a status message (placeholder for now)"""
        logger.info(message) 