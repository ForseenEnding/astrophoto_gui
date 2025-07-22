from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QDialogButtonBox, QGroupBox, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QSplitter, QComboBox, QTabWidget, QSpinBox, QDoubleSpinBox, QWidget
)
from PySide6.QtCore import Qt, Signal
from core.equipment.equipment import equipment_manager, Telescope, Camera
import logging

logger = logging.getLogger(__name__)

class EquipmentDialog(QDialog):
    """Dialog for managing equipment - adding, editing, and deleting telescopes and cameras"""
    
    equipment_updated = Signal()  # Signal when equipment is modified
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_equipment()
        
    def setup_ui(self):
        self.setWindowTitle("Equipment Management")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Tab widget for telescopes and cameras
        tab_widget = QTabWidget()
        
        # Telescope tab
        telescope_tab = self.create_telescope_tab()
        tab_widget.addTab(telescope_tab, "Telescopes")
        
        # Camera tab
        camera_tab = self.create_camera_tab()
        tab_widget.addTab(camera_tab, "Cameras")
        
        layout.addWidget(tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def create_telescope_tab(self):
        """Create the telescope management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Splitter for telescope list and form
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Telescope list
        list_group = QGroupBox("Telescopes")
        list_layout = QVBoxLayout(list_group)
        
        self.telescope_list = QListWidget()
        self.telescope_list.setStyleSheet("""
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
        self.telescope_list.itemSelectionChanged.connect(self.on_telescope_selected)
        list_layout.addWidget(self.telescope_list)
        
        # Telescope action buttons
        telescope_btn_layout = QHBoxLayout()
        
        self.add_telescope_btn = QPushButton("Add")
        self.add_telescope_btn.setStyleSheet("""
            QPushButton {
                background-color: #006600;
                border: 1px solid #008800;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #007700;
            }
        """)
        self.add_telescope_btn.clicked.connect(self.add_telescope)
        telescope_btn_layout.addWidget(self.add_telescope_btn)
        
        self.edit_telescope_btn = QPushButton("Edit")
        self.edit_telescope_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #444444;
                border-color: #555555;
                color: #888888;
            }
        """)
        self.edit_telescope_btn.clicked.connect(self.edit_telescope)
        self.edit_telescope_btn.setEnabled(False)
        telescope_btn_layout.addWidget(self.edit_telescope_btn)
        
        self.delete_telescope_btn = QPushButton("Delete")
        self.delete_telescope_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #444444;
                border-color: #555555;
                color: #888888;
            }
        """)
        self.delete_telescope_btn.clicked.connect(self.delete_telescope)
        self.delete_telescope_btn.setEnabled(False)
        telescope_btn_layout.addWidget(self.delete_telescope_btn)
        
        list_layout.addLayout(telescope_btn_layout)
        splitter.addWidget(list_group)
        
        # Right side - Telescope form
        form_group = QGroupBox("Telescope Details")
        form_layout = QVBoxLayout(form_group)
        
        self.telescope_form = QFormLayout()
        
        self.telescope_name_edit = QLineEdit()
        self.telescope_name_edit.setPlaceholderText("Enter telescope name")
        self.telescope_name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 10px;
            }
        """)
        self.telescope_form.addRow("Name:", self.telescope_name_edit)
        
        self.focal_length_spin = QDoubleSpinBox()
        self.focal_length_spin.setRange(0, 10000)
        self.focal_length_spin.setSuffix(" mm")
        self.focal_length_spin.setDecimals(1)
        self.focal_length_spin.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 10px;
            }
        """)
        self.telescope_form.addRow("Focal Length:", self.focal_length_spin)
        
        self.aperture_spin = QDoubleSpinBox()
        self.aperture_spin.setRange(0, 1000)
        self.aperture_spin.setSuffix(" mm")
        self.aperture_spin.setDecimals(1)
        self.aperture_spin.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 10px;
            }
        """)
        self.telescope_form.addRow("Aperture:", self.aperture_spin)
        
        # Focal ratio display (read-only)
        self.focal_ratio_label = QLabel("0.0")
        self.focal_ratio_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        self.telescope_form.addRow("Focal Ratio (f/):", self.focal_ratio_label)
        
        # Connect spinboxes to update focal ratio
        self.focal_length_spin.valueChanged.connect(self.update_focal_ratio)
        self.aperture_spin.valueChanged.connect(self.update_focal_ratio)
        
        form_layout.addLayout(self.telescope_form)
        
        # Save/Cancel buttons for telescope
        telescope_form_btn_layout = QHBoxLayout()
        
        self.save_telescope_btn = QPushButton("Save")
        self.save_telescope_btn.setStyleSheet("""
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
        """)
        self.save_telescope_btn.clicked.connect(self.save_telescope)
        telescope_form_btn_layout.addWidget(self.save_telescope_btn)
        
        self.cancel_telescope_btn = QPushButton("Cancel")
        self.cancel_telescope_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                border: 1px solid #888888;
                border-radius: 4px;
                color: #ffffff;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        self.cancel_telescope_btn.clicked.connect(self.cancel_telescope_edit)
        telescope_form_btn_layout.addWidget(self.cancel_telescope_btn)
        
        form_layout.addLayout(telescope_form_btn_layout)
        splitter.addWidget(form_group)
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
        # Store references for telescope management
        self.current_telescope = None
        self.telescope_edit_mode = False
        
        return widget
        
    def create_camera_tab(self):
        """Create the camera management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Splitter for camera list and form
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Camera list
        list_group = QGroupBox("Cameras")
        list_layout = QVBoxLayout(list_group)
        
        self.camera_list = QListWidget()
        self.camera_list.setStyleSheet("""
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
        self.camera_list.itemSelectionChanged.connect(self.on_camera_selected)
        list_layout.addWidget(self.camera_list)
        
        # Camera action buttons
        camera_btn_layout = QHBoxLayout()
        
        self.add_camera_btn = QPushButton("Add")
        self.add_camera_btn.setStyleSheet("""
            QPushButton {
                background-color: #006600;
                border: 1px solid #008800;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #007700;
            }
        """)
        self.add_camera_btn.clicked.connect(self.add_camera)
        camera_btn_layout.addWidget(self.add_camera_btn)
        
        self.edit_camera_btn = QPushButton("Edit")
        self.edit_camera_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #444444;
                border-color: #555555;
                color: #888888;
            }
        """)
        self.edit_camera_btn.clicked.connect(self.edit_camera)
        self.edit_camera_btn.setEnabled(False)
        camera_btn_layout.addWidget(self.edit_camera_btn)
        
        self.delete_camera_btn = QPushButton("Delete")
        self.delete_camera_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #444444;
                border-color: #555555;
                color: #888888;
            }
        """)
        self.delete_camera_btn.clicked.connect(self.delete_camera)
        self.delete_camera_btn.setEnabled(False)
        camera_btn_layout.addWidget(self.delete_camera_btn)
        
        list_layout.addLayout(camera_btn_layout)
        splitter.addWidget(list_group)
        
        # Right side - Camera form
        form_group = QGroupBox("Camera Details")
        form_layout = QVBoxLayout(form_group)
        
        self.camera_form = QFormLayout()
        
        self.camera_name_edit = QLineEdit()
        self.camera_name_edit.setPlaceholderText("Enter camera name")
        self.camera_name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 10px;
            }
        """)
        self.camera_form.addRow("Name:", self.camera_name_edit)
        
        self.sensor_width_spin = QDoubleSpinBox()
        self.sensor_width_spin.setRange(0, 100)
        self.sensor_width_spin.setSuffix(" mm")
        self.sensor_width_spin.setDecimals(2)
        self.sensor_width_spin.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 10px;
            }
        """)
        self.camera_form.addRow("Sensor Width:", self.sensor_width_spin)
        
        self.sensor_height_spin = QDoubleSpinBox()
        self.sensor_height_spin.setRange(0, 100)
        self.sensor_height_spin.setSuffix(" mm")
        self.sensor_height_spin.setDecimals(2)
        self.sensor_height_spin.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 10px;
            }
        """)
        self.camera_form.addRow("Sensor Height:", self.sensor_height_spin)
        
        self.pixel_size_spin = QDoubleSpinBox()
        self.pixel_size_spin.setRange(0, 100)
        self.pixel_size_spin.setSuffix(" μm")
        self.pixel_size_spin.setDecimals(2)
        self.pixel_size_spin.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 10px;
            }
        """)
        self.camera_form.addRow("Pixel Size:", self.pixel_size_spin)
        
        self.pixel_width_spin = QSpinBox()
        self.pixel_width_spin.setRange(0, 100000)
        self.pixel_width_spin.setStyleSheet("""
            QSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 10px;
            }
        """)
        self.camera_form.addRow("Pixel Width:", self.pixel_width_spin)
        
        self.pixel_height_spin = QSpinBox()
        self.pixel_height_spin.setRange(0, 100000)
        self.pixel_height_spin.setStyleSheet("""
            QSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 10px;
            }
        """)
        self.camera_form.addRow("Pixel Height:", self.pixel_height_spin)
        
        self.diffraction_limit_spin = QDoubleSpinBox()
        self.diffraction_limit_spin.setRange(0, 10)
        self.diffraction_limit_spin.setSuffix(" arcsec")
        self.diffraction_limit_spin.setDecimals(3)
        self.diffraction_limit_spin.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
                font-size: 10px;
            }
        """)
        self.camera_form.addRow("Diffraction Limit:", self.diffraction_limit_spin)
        
        # Total pixels display (read-only)
        self.total_pixels_label = QLabel("0")
        self.total_pixels_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        self.camera_form.addRow("Total Pixels:", self.total_pixels_label)
        
        # Connect spinboxes to update total pixels
        self.pixel_width_spin.valueChanged.connect(self.update_total_pixels)
        self.pixel_height_spin.valueChanged.connect(self.update_total_pixels)
        
        form_layout.addLayout(self.camera_form)
        
        # Save/Cancel buttons for camera
        camera_form_btn_layout = QHBoxLayout()
        
        self.save_camera_btn = QPushButton("Save")
        self.save_camera_btn.setStyleSheet("""
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
        """)
        self.save_camera_btn.clicked.connect(self.save_camera)
        camera_form_btn_layout.addWidget(self.save_camera_btn)
        
        self.cancel_camera_btn = QPushButton("Cancel")
        self.cancel_camera_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                border: 1px solid #888888;
                border-radius: 4px;
                color: #ffffff;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        self.cancel_camera_btn.clicked.connect(self.cancel_camera_edit)
        camera_form_btn_layout.addWidget(self.cancel_camera_btn)
        
        form_layout.addLayout(camera_form_btn_layout)
        splitter.addWidget(form_group)
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
        # Store references for camera management
        self.current_camera = None
        self.camera_edit_mode = False
        
        return widget
        
    def load_equipment(self):
        """Load equipment into lists"""
        self.load_telescopes()
        self.load_cameras()
        
    def load_telescopes(self):
        """Load telescopes into the list"""
        self.telescope_list.clear()
        
        for telescope in equipment_manager.get_all_telescopes():
            item = QListWidgetItem(f"{telescope.name} (f/{telescope.focal_ratio:.1f})")
            item.setData(Qt.UserRole, telescope)
            self.telescope_list.addItem(item)
            
    def load_cameras(self):
        """Load cameras into the list"""
        self.camera_list.clear()
        
        for camera in equipment_manager.get_all_cameras():
            item = QListWidgetItem(f"{camera.name} ({camera.pixel_width}x{camera.pixel_height})")
            item.setData(Qt.UserRole, camera)
            self.camera_list.addItem(item)
            
    # Telescope management methods
    def on_telescope_selected(self):
        """Handle telescope selection in the list"""
        current_item = self.telescope_list.currentItem()
        has_selection = current_item is not None
        
        self.edit_telescope_btn.setEnabled(has_selection)
        self.delete_telescope_btn.setEnabled(has_selection)
        
        if has_selection and not self.telescope_edit_mode:
            telescope = current_item.data(Qt.UserRole)
            self.display_telescope(telescope)
            
    def display_telescope(self, telescope):
        """Display telescope data in the form"""
        self.telescope_name_edit.setText(telescope.name)
        self.focal_length_spin.setValue(telescope.focal_length)
        self.aperture_spin.setValue(telescope.aperture)
        self.update_focal_ratio()
        
    def update_focal_ratio(self):
        """Update the focal ratio display"""
        focal_length = self.focal_length_spin.value()
        aperture = self.aperture_spin.value()
        
        if aperture > 0:
            focal_ratio = focal_length / aperture
            self.focal_ratio_label.setText(f"{focal_ratio:.1f}")
        else:
            self.focal_ratio_label.setText("0.0")
            
    def add_telescope(self):
        """Add a new telescope"""
        self.telescope_edit_mode = True
        self.current_telescope = None
        self.clear_telescope_form()
        self.telescope_name_edit.setFocus()
        
    def edit_telescope(self):
        """Edit the selected telescope"""
        current_item = self.telescope_list.currentItem()
        if not current_item:
            return
            
        self.current_telescope = current_item.data(Qt.UserRole)
        self.telescope_edit_mode = True
        self.display_telescope(self.current_telescope)
        self.telescope_name_edit.setFocus()
        
    def save_telescope(self):
        """Save telescope changes"""
        name = self.telescope_name_edit.text().strip()
        focal_length = self.focal_length_spin.value()
        aperture = self.aperture_spin.value()
        
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a telescope name.")
            return
            
        if focal_length <= 0 or aperture <= 0:
            QMessageBox.warning(self, "Invalid Values", "Focal length and aperture must be greater than 0.")
            return
            
        try:
            if self.current_telescope:
                # Update existing telescope
                equipment_manager.update_telescope(
                    self.current_telescope.name,
                    name=name,
                    focal_length=focal_length,
                    aperture=aperture
                )
                logger.info(f"Updated telescope: {name}")
            else:
                # Create new telescope
                telescope = Telescope(name, focal_length, aperture, focal_length / aperture)
                equipment_manager.add_telescope(telescope)
                logger.info(f"Added telescope: {name}")
                
            self.load_telescopes()
            self.clear_telescope_form()
            self.telescope_edit_mode = False
            self.current_telescope = None
            self.equipment_updated.emit()
            
        except Exception as e:
            logger.error(f"Failed to save telescope: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save telescope: {e}")
            
    def cancel_telescope_edit(self):
        """Cancel telescope editing"""
        self.clear_telescope_form()
        self.telescope_edit_mode = False
        self.current_telescope = None
        
        # Restore display of selected telescope
        current_item = self.telescope_list.currentItem()
        if current_item:
            telescope = current_item.data(Qt.UserRole)
            self.display_telescope(telescope)
            
    def clear_telescope_form(self):
        """Clear the telescope form"""
        self.telescope_name_edit.clear()
        self.focal_length_spin.setValue(0)
        self.aperture_spin.setValue(0)
        self.focal_ratio_label.setText("0.0")
        
    def delete_telescope(self):
        """Delete the selected telescope"""
        current_item = self.telescope_list.currentItem()
        if not current_item:
            return
            
        telescope = current_item.data(Qt.UserRole)
        if not telescope:
            return
            
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            f"Are you sure you want to delete the telescope '{telescope.name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                equipment_manager.remove_telescope(telescope.name)
                self.load_telescopes()
                self.clear_telescope_form()
                self.equipment_updated.emit()
                logger.info(f"Deleted telescope: {telescope.name}")
                
            except Exception as e:
                logger.error(f"Failed to delete telescope: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete telescope: {e}")
                
    # Camera management methods
    def on_camera_selected(self):
        """Handle camera selection in the list"""
        current_item = self.camera_list.currentItem()
        has_selection = current_item is not None
        
        self.edit_camera_btn.setEnabled(has_selection)
        self.delete_camera_btn.setEnabled(has_selection)
        
        if has_selection and not self.camera_edit_mode:
            camera = current_item.data(Qt.UserRole)
            self.display_camera(camera)
            
    def display_camera(self, camera):
        """Display camera data in the form"""
        self.camera_name_edit.setText(camera.name)
        self.sensor_width_spin.setValue(camera.sensor_width)
        self.sensor_height_spin.setValue(camera.sensor_height)
        self.pixel_size_spin.setValue(camera.pixel_size)
        self.pixel_width_spin.setValue(camera.pixel_width)
        self.pixel_height_spin.setValue(camera.pixel_height)
        self.diffraction_limit_spin.setValue(camera.diffraction_limit)
        self.update_total_pixels()
        
    def update_total_pixels(self):
        """Update the total pixels display"""
        width = self.pixel_width_spin.value()
        height = self.pixel_height_spin.value()
        total = width * height
        self.total_pixels_label.setText(f"{total:,}")
        
    def add_camera(self):
        """Add a new camera"""
        self.camera_edit_mode = True
        self.current_camera = None
        self.clear_camera_form()
        self.camera_name_edit.setFocus()
        
    def edit_camera(self):
        """Edit the selected camera"""
        current_item = self.camera_list.currentItem()
        if not current_item:
            return
            
        self.current_camera = current_item.data(Qt.UserRole)
        self.camera_edit_mode = True
        self.display_camera(self.current_camera)
        self.camera_name_edit.setFocus()
        
    def save_camera(self):
        """Save camera changes"""
        name = self.camera_name_edit.text().strip()
        sensor_width = self.sensor_width_spin.value()
        sensor_height = self.sensor_height_spin.value()
        pixel_size = self.pixel_size_spin.value()
        pixel_width = self.pixel_width_spin.value()
        pixel_height = self.pixel_height_spin.value()
        diffraction_limit = self.diffraction_limit_spin.value()
        
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a camera name.")
            return
            
        if sensor_width <= 0 or sensor_height <= 0 or pixel_size <= 0:
            QMessageBox.warning(self, "Invalid Values", "Sensor dimensions and pixel size must be greater than 0.")
            return
            
        if pixel_width <= 0 or pixel_height <= 0:
            QMessageBox.warning(self, "Invalid Values", "Pixel dimensions must be greater than 0.")
            return
            
        try:
            if self.current_camera:
                # Update existing camera
                equipment_manager.update_camera(
                    self.current_camera.name,
                    name=name,
                    sensor_width=sensor_width,
                    sensor_height=sensor_height,
                    pixel_size=pixel_size,
                    pixel_width=pixel_width,
                    pixel_height=pixel_height,
                    diffraction_limit=diffraction_limit
                )
                logger.info(f"Updated camera: {name}")
            else:
                # Create new camera
                camera = Camera(name, sensor_width, sensor_height, pixel_size, 
                              pixel_width, pixel_height, diffraction_limit)
                equipment_manager.add_camera(camera)
                logger.info(f"Added camera: {name}")
                
            self.load_cameras()
            self.clear_camera_form()
            self.camera_edit_mode = False
            self.current_camera = None
            self.equipment_updated.emit()
            
        except Exception as e:
            logger.error(f"Failed to save camera: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save camera: {e}")
            
    def cancel_camera_edit(self):
        """Cancel camera editing"""
        self.clear_camera_form()
        self.camera_edit_mode = False
        self.current_camera = None
        
        # Restore display of selected camera
        current_item = self.camera_list.currentItem()
        if current_item:
            camera = current_item.data(Qt.UserRole)
            self.display_camera(camera)
            
    def clear_camera_form(self):
        """Clear the camera form"""
        self.camera_name_edit.clear()
        self.sensor_width_spin.setValue(0)
        self.sensor_height_spin.setValue(0)
        self.pixel_size_spin.setValue(0)
        self.pixel_width_spin.setValue(0)
        self.pixel_height_spin.setValue(0)
        self.diffraction_limit_spin.setValue(0)
        self.total_pixels_label.setText("0")
        
    def delete_camera(self):
        """Delete the selected camera"""
        current_item = self.camera_list.currentItem()
        if not current_item:
            return
            
        camera = current_item.data(Qt.UserRole)
        if not camera:
            return
            
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            f"Are you sure you want to delete the camera '{camera.name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                equipment_manager.remove_camera(camera.name)
                self.load_cameras()
                self.clear_camera_form()
                self.equipment_updated.emit()
                logger.info(f"Deleted camera: {camera.name}")
                
            except Exception as e:
                logger.error(f"Failed to delete camera: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete camera: {e}") 