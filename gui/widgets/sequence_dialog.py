from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QSpinBox, QDoubleSpinBox, QDialogButtonBox, QGroupBox
)
from PySide6.QtCore import Qt
from core.sequence.sequence import Sequence, sequence_manager
from core.camera.camera_settings import SettingProfile
from gui.widgets.setting_profile_box import SettingProfileBox, ProfileMode
import logging

logger = logging.getLogger(__name__)

class SequenceDialog(QDialog):
    """Dialog for creating and editing sequences"""
    
    def __init__(self, session_id: str, sequence: Sequence = None, parent=None):
        super().__init__(parent)
        self.session_id = session_id
        self.sequence = sequence
        self.setup_ui()
        self.load_sequence_data()
        
    def setup_ui(self):
        self.setWindowTitle("Sequence Editor" if self.sequence else "Create Sequence")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Sequence information
        info_group = QGroupBox("Sequence Information")
        info_layout = QFormLayout(info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter sequence name")
        info_layout.addRow("Name:", self.name_edit)
        
        self.exposure_count_spin = QSpinBox()
        self.exposure_count_spin.setRange(1, 1000)
        self.exposure_count_spin.setValue(10)
        info_layout.addRow("Exposure Count:", self.exposure_count_spin)
        
        self.exposure_time_spin = QDoubleSpinBox()
        self.exposure_time_spin.setRange(0.1, 3600.0)
        self.exposure_time_spin.setValue(30.0)
        self.exposure_time_spin.setSuffix(" s")
        info_layout.addRow("Exposure Time:", self.exposure_time_spin)
        
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.0, 3600.0)
        self.interval_spin.setValue(5.0)
        self.interval_spin.setSuffix(" s")
        info_layout.addRow("Interval:", self.interval_spin)
        
        layout.addWidget(info_group)
        
        # Settings profile
        settings_group = QGroupBox("Camera Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        self.settings_box = SettingProfileBox(mode=ProfileMode.EDIT)
        settings_layout.addWidget(self.settings_box)
        
        layout.addWidget(settings_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_sequence_data(self):
        """Load existing sequence data if editing"""
        if self.sequence:
            self.name_edit.setText(self.sequence.name)
            self.exposure_count_spin.setValue(self.sequence.exposure_count)
            self.exposure_time_spin.setValue(self.sequence.exposure_time)
            self.interval_spin.setValue(self.sequence.interval)
            if self.sequence.settings:
                self.settings_box.set_setting_profile(self.sequence.settings)
    
    def get_sequence_data(self) -> dict:
        """Get the sequence data from the form"""
        return {
            "name": self.name_edit.text().strip(),
            "exposure_count": self.exposure_count_spin.value(),
            "exposure_time": self.exposure_time_spin.value(),
            "interval": self.interval_spin.value(),
            "settings": self.settings_box.setting_profile
        }
    
    def accept(self):
        """Validate and accept the dialog"""
        data = self.get_sequence_data()
        
        if not data["name"]:
            logger.warning("Sequence name cannot be empty")
            return
        
        if data["exposure_count"] < 1:
            logger.warning("Exposure count must be at least 1")
            return
        
        if data["exposure_time"] <= 0:
            logger.warning("Exposure time must be greater than 0")
            return
        
        if data["interval"] < 0:
            logger.warning("Interval cannot be negative")
            return
        
        super().accept() 