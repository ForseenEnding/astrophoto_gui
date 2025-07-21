from PySide6.QtWidgets import (
    QGroupBox, QFormLayout, QComboBox, QCheckBox, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QDialog, QListWidget, QListWidgetItem, QDialogButtonBox, QSplitter, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from core.camera.camera_settings import SettingProfile, camera_settings, Type, default_profile, settings_profiles
import logging  
from enum import Enum

logger = logging.getLogger(__name__)

class ProfileMode(Enum):
    DISPLAY = "display"    # Display only a specific profile, readonly
    SELECT = "select"      # Select and apply profiles, readonly settings
    EDIT = "edit"          # Full profile management with editing

class SettingBuilderDialog(QDialog):
    """Dialog for building and managing profile settings"""
    
    profiles_changed = Signal()  # Signal to notify when profiles are added/deleted
    
    def __init__(self, current_profile: SettingProfile, parent=None):
        super().__init__(parent)
        self.current_profile = current_profile
        self.selected_settings = set(self.current_profile.settings.keys())
        self.setup_ui()
        self.load_available_settings()
        
    def setup_ui(self):
        self.setWindowTitle("Profile Setting Builder")
        self.setModal(True)
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Profile management section
        profile_group = QGroupBox("Profile Management")
        profile_group.setFixedHeight(60)  # Set fixed height to prevent stretching
        profile_layout = QHBoxLayout(profile_group)
        profile_layout.setContentsMargins(10, 5, 10, 5)  # Reduce vertical margins
        
        # Profile selection
        profile_layout.addWidget(QLabel("Profile:"))
        
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px;
                min-width: 150px;
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
        self.profile_combo.currentIndexChanged.connect(self.on_profile_changed)
        profile_layout.addWidget(self.profile_combo)
        
        # New profile name input
        profile_layout.addWidget(QLabel("New Profile:"))
        self.new_profile_name = QLineEdit()
        self.new_profile_name.setPlaceholderText("Enter profile name")
        self.new_profile_name.setStyleSheet("""
            QLineEdit {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px;
                min-width: 120px;
                font-size: 10px;
            }
        """)
        profile_layout.addWidget(self.new_profile_name)
        
        # Create profile button
        self.create_profile_btn = QPushButton("Create")
        self.create_profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #006600;
                border: 1px solid #008800;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #007700;
            }
            QPushButton:pressed {
                background-color: #005500;
            }
        """)
        self.create_profile_btn.clicked.connect(self.create_new_profile)
        profile_layout.addWidget(self.create_profile_btn)
        
        # Delete profile button
        self.delete_profile_btn = QPushButton("Delete")
        self.delete_profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #cc0000;
                border: 1px solid #ee0000;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #dd0000;
            }
            QPushButton:pressed {
                background-color: #bb0000;
            }
        """)
        self.delete_profile_btn.clicked.connect(self.delete_current_profile)
        profile_layout.addWidget(self.delete_profile_btn)
        
        
        layout.addWidget(profile_group)
        
        # Splitter for available and selected settings
        splitter = QSplitter(Qt.Horizontal)
        
        # Available settings panel
        available_group = QGroupBox("Available Settings")
        available_layout = QVBoxLayout(available_group)
        
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.SingleSelection)
        available_layout.addWidget(self.available_list)
        
        # Add button
        add_btn = QPushButton("Add →")
        add_btn.clicked.connect(self.add_selected_setting)
        available_layout.addWidget(add_btn)
        
        splitter.addWidget(available_group)
        
        # Selected settings panel
        selected_group = QGroupBox("Profile Settings")
        selected_layout = QVBoxLayout(selected_group)
        
        self.selected_list = QListWidget()
        self.selected_list.setSelectionMode(QListWidget.SingleSelection)
        selected_layout.addWidget(self.selected_list)
        
        # Remove button
        remove_btn = QPushButton("← Remove")
        remove_btn.clicked.connect(self.remove_selected_setting)
        selected_layout.addWidget(remove_btn)
        
        splitter.addWidget(selected_group)
        
        layout.addWidget(splitter)
        
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Initialize profile list
        self.load_profile_list()
        
    def load_available_settings(self):
        """Load available settings into the lists"""
        # Clear existing items first to prevent duplicates
        self.available_list.clear()
        self.selected_list.clear()
        
        all_settings = camera_settings.get_settings()
        current_setting_names = set(self.current_profile.settings.keys())
        
        # Populate available settings
        for setting in all_settings:
            if not setting.readonly and setting.name not in current_setting_names:
                item = QListWidgetItem(f"{setting.label} ({setting.name})")
                item.setData(Qt.UserRole, setting)
                self.available_list.addItem(item)
        
        # Populate selected settings
        for setting_name in self.current_profile.settings.keys():
            setting = camera_settings.get_setting(setting_name)
            if setting:
                item = QListWidgetItem(f"{setting.label} ({setting.name})")
                item.setData(Qt.UserRole, setting)
                self.selected_list.addItem(item)
    
    def add_selected_setting(self):
        """Add the selected setting from available to selected"""
        current_item = self.available_list.currentItem()
        if current_item:
            setting = current_item.data(Qt.UserRole)
            self.selected_settings.add(setting.name)
            
            # Move item to selected list
            self.selected_list.addItem(self.available_list.takeItem(self.available_list.row(current_item)))
    
    def remove_selected_setting(self):
        """Remove the selected setting from selected to available"""
        current_item = self.selected_list.currentItem()
        if current_item:
            setting = current_item.data(Qt.UserRole)
            self.selected_settings.discard(setting.name)
            
            # Move item to available list
            self.available_list.addItem(self.selected_list.takeItem(self.selected_list.row(current_item)))
    
    def get_updated_profile(self) -> SettingProfile:
        """Get the updated profile with the new setting selection"""
        # Keep existing values for settings that are still selected
        new_settings = {}
        for setting_name in self.selected_settings:
            if setting_name in self.current_profile.settings:
                new_settings[setting_name] = self.current_profile.settings[setting_name]
            else:
                # Add new setting with default value
                setting = camera_settings.get_setting(setting_name)
                if setting:
                    new_settings[setting_name] = setting.default_value
        
        return SettingProfile(name=self.current_profile.name, settings=new_settings)

    def load_profile_list(self):
        """Load profiles into the profile combo box"""
        self.profile_combo.clear()
        for profile in settings_profiles.get_profiles():
            self.profile_combo.addItem(profile.name, profile)
        # Add default option if no profiles exist
        if self.profile_combo.count() == 0:
            self.profile_combo.addItem("Default", default_profile)
        
        # Set current profile as selected
        for i in range(self.profile_combo.count()):
            profile = self.profile_combo.itemData(i)
            if profile and profile.name == self.current_profile.name:
                self.profile_combo.setCurrentIndex(i)
                break
        else:
            self.profile_combo.setCurrentIndex(0)

    def on_profile_changed(self, index):
        """Handle profile selection change"""
        profile = self.profile_combo.currentData()
        if profile:
            self.current_profile = profile
            self.selected_settings = set(self.current_profile.settings.keys())
            self.new_profile_name.clear()
            self.delete_profile_btn.setEnabled(profile != default_profile)
            self.load_available_settings()
            logger.info(f"Profile changed to: {self.current_profile.name}")
        else:
            self.current_profile = default_profile
            self.selected_settings = set(self.current_profile.settings.keys())
            self.new_profile_name.clear()
            self.delete_profile_btn.setEnabled(False)
            self.load_available_settings()
            logger.info(f"Profile changed to default: {self.current_profile.name}")

    def create_new_profile(self):
        """Create a new profile with the entered name"""
        new_name = self.new_profile_name.text().strip()
        if not new_name:
            logger.warning("Profile name cannot be empty.")
            return

        if settings_profiles.get_profile(new_name):
            logger.warning(f"Profile with name '{new_name}' already exists.")
            return

        new_profile = SettingProfile(name=new_name, settings={})
        if settings_profiles.add_profile(new_profile):
            logger.info(f"Profile '{new_profile.name}' created successfully.")
            self.load_profile_list()
            # Select the newly created profile
            for i in range(self.profile_combo.count()):
                profile = self.profile_combo.itemData(i)
                if profile and profile.name == new_name:
                    self.profile_combo.setCurrentIndex(i)
                    break
            # Emit signal to notify parent widget
            self.profiles_changed.emit()
        else:
            logger.error(f"Failed to create profile '{new_profile.name}'.")

    def delete_current_profile(self):
        """Delete the currently selected profile"""
        if self.current_profile == default_profile:
            logger.warning("Cannot delete the default profile.")
            return

        settings_profiles.remove_profile(self.current_profile.name)
        logger.info(f"Profile '{self.current_profile.name}' deleted successfully.")
        self.load_profile_list()
        # Emit signal to notify parent widget
        self.profiles_changed.emit()

class SettingProfileBox(QGroupBox):
    
    setting_profile_changed = Signal(SettingProfile)
    
    """A box that displays a setting profile with three modes:
    - DISPLAY: Shows a specific profile in readonly mode
    - SELECT: Allows selecting and applying profiles, settings are readonly
    - EDIT: Full profile management with editing
    """
    def __init__(self, mode: ProfileMode = ProfileMode.SELECT, profile: SettingProfile = None):
        super().__init__(title="Setting Profile")
        self.mode = mode
        self.setting_profile = profile or default_profile
        self.controls = {}  # Store controls for later access
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI based on the mode"""
        if self.mode == ProfileMode.DISPLAY:
            self.setup_display_mode()
        elif self.mode == ProfileMode.SELECT:
            self.setup_select_mode()
        elif self.mode == ProfileMode.EDIT:
            self.setup_edit_mode()
    
    def setup_display_mode(self):
        """Setup display mode - shows specific profile in readonly"""
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        
        # Profile info
        profile_info = QLabel(f"Profile: {self.setting_profile.name}")
        profile_info.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 11px;")
        self.layout.addWidget(profile_info)
        
        # Settings widget
        self.settings_widget = QGroupBox("Settings")
        self.settings_layout = QFormLayout(self.settings_widget)
        self.settings_layout.setAlignment(Qt.AlignTop)
        self.layout.addWidget(self.settings_widget)
        
        # Apply button
        self.save_profile_btn = QPushButton("Save")
        self.save_profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #006600;
                border: 1px solid #008800;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #007700;
            }
            QPushButton:pressed {
                background-color: #005500;
            }
        """)
        self.save_profile_btn.clicked.connect(self.apply_current_profile)
        self.layout.addWidget(self.save_profile_btn)
        
        self.update_ui()
    
    def setup_select_mode(self):
        """Setup select mode - select and apply profiles, readonly settings"""
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        
        # Profile selection layout
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Profile:"))
        
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px;
                min-width: 120px;
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
        self.profile_combo.currentIndexChanged.connect(self.on_profile_selected)
        profile_layout.addWidget(self.profile_combo)
        
        # Apply button
        self.save_profile_btn = QPushButton("Apply")
        self.save_profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #006600;
                border: 1px solid #008800;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #007700;
            }
            QPushButton:pressed {
                background-color: #005500;
            }
        """)
        self.save_profile_btn.clicked.connect(self.apply_current_profile)
        profile_layout.addWidget(self.save_profile_btn)
        
        # Add some spacing
        profile_layout.addStretch()
        
        self.layout.addLayout(profile_layout)
        
        # Settings widget
        self.settings_widget = QGroupBox("Settings")
        self.settings_layout = QFormLayout(self.settings_widget)
        self.settings_layout.setAlignment(Qt.AlignTop)
        self.layout.addWidget(self.settings_widget)
        
        # Initialize
        self.update_profile_list()
        if self.profile_combo.count() > 0:
            self.profile_combo.setCurrentIndex(0)
        else:
            self.set_setting_profile(default_profile)
    
    def setup_edit_mode(self):
        """Setup edit mode - full profile management with editing"""
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        
        # Profile selection and apply row
        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel("Profile:"))
        
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px;
                min-width: 120px;
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
        self.profile_combo.currentIndexChanged.connect(self.on_profile_selected)
        profile_row.addWidget(self.profile_combo)
        
        # Apply button
        self.save_profile_btn = QPushButton("Save")
        self.save_profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #006600;
                border: 1px solid #008800;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #007700;
            }
            QPushButton:pressed {
                background-color: #005500;
            }
        """)
        self.save_profile_btn.clicked.connect(self.save_current_profile)
        profile_row.addWidget(self.save_profile_btn)
        
        # Add spacing between dropdown and button
        profile_row.addSpacing(10)
        
        self.layout.addLayout(profile_row)
        
        # Profile management buttons row
        management_row = QHBoxLayout()
        
        
        # Add Setting button
        self.modify_setting_btn = QPushButton("Modify Setting")
        self.modify_setting_btn.setStyleSheet("""
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
        self.modify_setting_btn.clicked.connect(self.add_new_setting)
        management_row.addWidget(self.modify_setting_btn)
        
        # Add spacing
        management_row.addStretch()
        
        self.layout.addLayout(management_row)
        
        # Settings widget
        self.settings_widget = QGroupBox("Settings")
        self.settings_layout = QFormLayout(self.settings_widget)
        self.settings_layout.setAlignment(Qt.AlignTop)
        self.layout.addWidget(self.settings_widget)
        
        # Initialize
        self.update_profile_list()
        if self.profile_combo.count() > 0:
            self.profile_combo.setCurrentIndex(0)
        else:
            self.set_setting_profile(default_profile)
    
    def update_profile_list(self):
        """Update the profile selection combo box"""
        if hasattr(self, 'profile_combo'):
            self.profile_combo.clear()
            
            for profile in settings_profiles.get_profiles():
                logger.debug(f"Profile: {profile.name}")
                self.profile_combo.addItem(profile.name, profile)
            
            # Add default option if no profiles exist
            if self.profile_combo.count() == 0:
                self.profile_combo.addItem("Default", default_profile)
            
    def on_profile_selected(self, index):
        """Handle profile selection"""
        if hasattr(self, 'profile_combo'):
            profile = self.profile_combo.currentData()
            if profile:
                self.set_setting_profile(profile)
            else:
                self.set_setting_profile(default_profile)
        
    def set_setting_profile(self, setting_profile: SettingProfile):
        self.setting_profile = setting_profile
        self.setting_profile_changed.emit(setting_profile)
        self.update_ui()
        
        
    def update_ui(self):
        # Clear existing controls
        while self.settings_layout.rowCount() > 0:
            self.settings_layout.removeRow(0)
        self.controls.clear()   
        
        if not self.setting_profile:
            return
            
        # Create controls for each setting in the profile
        for setting_name, value in self.setting_profile.settings.items():
            setting = camera_settings.get_setting(setting_name)
            if setting and not setting.readonly:
                control = self.create_setting_control(setting, value)
                if control:
                    self.controls[setting_name] = control
                    self.settings_layout.addRow(f"{setting.label}:", control)
    
    def create_setting_control(self, setting, current_value):
        """Create a control widget for a camera setting"""
        if setting.type == Type.RADIO or setting.type == Type.MENU:
            # Create combo box for radio/menu settings
            combo = QComboBox()
            combo.setStyleSheet("""
                QComboBox {
                    background-color: #3a3a3a;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    color: #ffffff;
                    padding: 4px;
                    min-width: 100px;
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
            
            # Add choices from setting
            if setting.choices:
                combo.addItems(setting.choices)
            
            # Set current value from profile
            if current_value in setting.choices:
                combo.setCurrentText(current_value)
            elif setting.choices:
                combo.setCurrentIndex(0)
            
            # Disable if not in edit mode
            if self.mode != ProfileMode.EDIT:
                combo.setDisabled(True)
                
            return combo
            
        elif setting.type == Type.TOGGLE:
            # Create checkbox for toggle settings
            checkbox = QCheckBox()
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #ffffff;
                    font-size: 10px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #3a3a3a;
                    border: 1px solid #555555;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    background-color: #006600;
                    border: 1px solid #008800;
                    border-radius: 3px;
                }
            """)
            
            # Set current value from profile
            checkbox.setChecked(current_value == "1" or current_value == "true")
            
            # Disable if not in edit mode
            if self.mode != ProfileMode.EDIT:
                checkbox.setDisabled(True)
            return checkbox
            
        elif setting.type == Type.TEXT:
            # Create line edit for text settings
            line_edit = QLineEdit()
            line_edit.setStyleSheet("""
                QLineEdit {
                    background-color: #3a3a3a;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    color: #ffffff;
                    padding: 4px;
                    min-width: 100px;
                    font-size: 10px;
                }
            """)
            
            # Set current value from profile
            line_edit.setText(current_value)
            
            # Make readonly if not in edit mode
            if self.mode != ProfileMode.EDIT:
                line_edit.setReadOnly(True)
            return line_edit
        
        return None
    
    def get_current_values(self) -> dict[str, str]:
        """Get current values from all controls"""
        values = {}
        for setting_name, control in self.controls.items():
            if isinstance(control, QComboBox):
                values[setting_name] = control.currentText()
            elif isinstance(control, QCheckBox):
                values[setting_name] = "1" if control.isChecked() else "0"
            elif isinstance(control, QLineEdit):
                values[setting_name] = control.text()
        return values
    
    def create_profile_from_current(self, name: str) -> SettingProfile:
        """Create a new SettingProfile from current control values"""
        values = self.get_current_values()
        return SettingProfile(name=name, settings=values)
    
    
    def add_new_setting(self):
        """Add a new setting to the current profile using the setting builder dialog"""
        if not self.setting_profile or self.mode != ProfileMode.EDIT:
            return
            
        # Create and show the setting builder dialog
        dialog = SettingBuilderDialog(self.setting_profile, self)
        dialog.profiles_changed.connect(self.update_profile_list) # Connect signal to update profile list
        if dialog.exec() == QDialog.Accepted:
            # Get the updated profile from the dialog
            updated_profile = dialog.get_updated_profile()
            
            # Update our profile
            self.setting_profile = updated_profile
            self.update_ui()
            
            logger.info(f"Profile '{updated_profile.name}' updated with new settings.")

    def save_current_profile(self):
        """Save the current profile to settings_profiles"""
        if not self.setting_profile or self.mode != ProfileMode.EDIT:
            return

        # Get current values from controls
        current_values = self.get_current_values()
        
        # Create updated profile with current values
        updated_profile = SettingProfile(
            name=self.setting_profile.name,
            settings=current_values
        )
        
        # Update the profile in settings_profiles
        if settings_profiles.add_profile(updated_profile):
            logger.info(f"Profile '{updated_profile.name}' saved successfully.")
            # Update our local reference
            self.setting_profile = updated_profile
        else:
            logger.error(f"Failed to save profile '{updated_profile.name}'.")