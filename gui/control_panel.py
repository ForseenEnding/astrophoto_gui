from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QAction

# Import our tab components
from gui.tabs.camera_tab import CameraTab
from gui.tabs.session_tab import SessionTab
from gui.tabs.preview_tab import PreviewTab

class TabbedControlPanel(QWidget):
    """Tabbed control panel with collapsible functionality"""
    
    # Signals
    connect_clicked = Signal()
    disconnect_clicked = Signal()
    preview_clicked = Signal()
    panel_toggled = Signal(bool)  # True when expanded, False when collapsed
    
    def __init__(self):
        super().__init__()
        self.is_expanded = True
        self.expanded_width = 300
        self.collapsed_width = 40
        self.previous_tab_index = -1
        self.setup_ui()
        self.setup_animations()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup the tabbed control panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create the main container
        self.container = QWidget()
        self.container.setFixedWidth(self.expanded_width)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Create tab widget with vertical tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.East)  # Tabs on the right side
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #2a2a2a;
                border-radius: 6px;
            }
            QTabWidget::tab-bar {
                alignment: right;
            }
            QTabBar::tab {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-left: none;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                padding: 8px 4px;
                margin-bottom: 2px;
                color: #ffffff;
                font-weight: bold;
                min-height: 80px;
                min-width: 30px;
            }
            QTabBar::tab:selected {
                background-color: #4a4a4a;
                border-color: #666666;
            }
            QTabBar::tab:hover {
                background-color: #5a5a5a;
            }
        """)
        
        # Connect tab change signal to handle collapse functionality
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Add keyboard shortcut for toggling panel
        self.toggle_shortcut = QAction("Toggle Control Panel", self)
        self.toggle_shortcut.setShortcut("Ctrl+P")
        self.toggle_shortcut.triggered.connect(self.toggle_panel)
        self.addAction(self.toggle_shortcut)
        
        # Create and add tabs in logical workflow order
        self.camera_tab = CameraTab()
        self.preview_tab = PreviewTab()
        self.session_tab = SessionTab()
        
        self.tab_widget.addTab(self.camera_tab, "Camera")
        self.tab_widget.addTab(self.preview_tab, "Preview")
        self.tab_widget.addTab(self.session_tab, "Session")
        
        # Set initial tab
        self.previous_tab_index = 0
        
        container_layout.addWidget(self.tab_widget)
        layout.addWidget(self.container)
        
        # Create toggle button
        self.toggle_button = QPushButton("▶")
        self.toggle_button.setFixedSize(self.collapsed_width, 60)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #ffffff;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border-color: #777777;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_panel)
        self.toggle_button.setToolTip("Expand Controls (Ctrl+P)")
        self.toggle_button.hide()  # Initially hidden since panel is expanded
        
        layout.addWidget(self.toggle_button)
        
        # Set initial size
        self.setFixedWidth(self.expanded_width)
        
    def setup_animations(self):
        """Setup animations for smooth collapse/expand"""
        self.expand_animation = QPropertyAnimation(self, b"minimumWidth")
        self.expand_animation.setDuration(300)
        self.expand_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.collapse_animation = QPropertyAnimation(self, b"minimumWidth")
        self.collapse_animation.setDuration(300)
        self.collapse_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Connect animation finished signals
        self.expand_animation.finished.connect(self.on_expand_finished)
        self.collapse_animation.finished.connect(self.on_collapse_finished)
        
    def setup_connections(self):
        """Setup signal connections between tabs and main panel"""
        # Camera tab connections
        self.camera_tab.connect_clicked.connect(self.connect_clicked.emit)
        self.camera_tab.disconnect_clicked.connect(self.disconnect_clicked.emit)
        self.camera_tab.preview_clicked.connect(self.preview_clicked.emit)
        
        # Preview tab connections
        self.preview_tab.aspect_ratio_changed.connect(lambda val: self.on_preview_aspect_ratio_changed(val))
        self.preview_tab.framerate_changed.connect(lambda val: self.on_preview_framerate_changed(val))
        self.preview_tab.zoom_changed.connect(lambda val: self.on_preview_zoom_changed(val))
        self.preview_tab.analysis_toggled.connect(lambda val: self.on_preview_analysis_toggled(val))
        
    def on_expand_finished(self):
        """Handle expand animation finished"""
        self.setFixedWidth(self.expanded_width)
        
    def on_collapse_finished(self):
        """Handle collapse animation finished"""
        self.setFixedWidth(self.collapsed_width)
        
    def expand_panel(self):
        """Expand the panel"""
        self.is_expanded = True
        self.toggle_button.setText("◀")
        self.toggle_button.setToolTip("Collapse Controls")
        self.toggle_button.hide()
        self.container.show()
        
        # Reset the previous tab index when expanding
        self.previous_tab_index = self.tab_widget.currentIndex()
        
        self.expand_animation.setStartValue(self.collapsed_width)
        self.expand_animation.setEndValue(self.expanded_width)
        self.expand_animation.start()
        
        self.panel_toggled.emit(True)
        
    def collapse_panel(self):
        """Collapse the panel"""
        self.is_expanded = False
        self.toggle_button.setText("▶")
        self.toggle_button.setToolTip("Expand Controls")
        self.toggle_button.show()
        self.container.hide()
        
        self.collapse_animation.setStartValue(self.expanded_width)
        self.collapse_animation.setEndValue(self.collapsed_width)
        self.collapse_animation.start()
        
        self.panel_toggled.emit(False)
        
    def toggle_panel(self):
        """Toggle the panel between expanded and collapsed states"""
        if self.is_expanded:
            self.collapse_panel()
        else:
            self.expand_panel()
            
    def on_tab_changed(self, index):
        """Handle tab changes - clicking an open tab collapses the panel"""
        if self.is_expanded and index == self.previous_tab_index:
            # If clicking the same tab that's already open, collapse the panel
            self.collapse_panel()
        else:
            # Update the previous tab index
            self.previous_tab_index = index

        
    def get_framerate(self) -> int:
        """Get framerate from session tab"""
        return self.session_tab.get_framerate()
        
    def increment_image_count(self):
        """Increment image count in session tab"""
        self.session_tab.increment_image_count()
        
    def add_exposure_time(self, exposure_seconds):
        """Add exposure time in session tab"""
        self.session_tab.add_exposure_time(exposure_seconds)
        
    def update_camera_status(self, status):
        """Update camera status in camera tab"""
        self.camera_tab.update_camera_status(status)

    # --- Preview tab signal handlers (to be connected externally) ---
    def on_preview_aspect_ratio_changed(self, keep):
        pass  # To be connected externally
    def on_preview_framerate_changed(self, fps):
        pass  # To be connected externally
    def on_preview_zoom_changed(self, zoom):
        pass  # To be connected externally
    def on_preview_analysis_toggled(self, enabled):
        pass  # To be connected externally

    def get_preview_aspect_ratio(self):
        return self.preview_tab.get_aspect_ratio()
    def get_preview_framerate(self):
        return self.preview_tab.get_framerate()
    def get_preview_zoom(self):
        return self.preview_tab.get_zoom()
    def is_preview_analysis_enabled(self):
        return self.preview_tab.is_analysis_enabled()
