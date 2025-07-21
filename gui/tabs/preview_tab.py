from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QSizePolicy, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal

class PreviewTab(QWidget):
    """Tab for preview settings and analysis toggle"""
    # Signals
    aspect_ratio_changed = Signal(bool)
    framerate_changed = Signal(int)
    zoom_changed = Signal(float)
    analysis_toggled = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title
        title_label = QLabel("Preview Settings")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        layout.addWidget(title_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #444444;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # Aspect ratio
        self.aspect_ratio_checkbox = QCheckBox("Keep Aspect Ratio")
        self.aspect_ratio_checkbox.setChecked(True)
        self.aspect_ratio_checkbox.setStyleSheet("color: #ffffff; font-size: 12px;")
        layout.addWidget(self.aspect_ratio_checkbox)

        # Framerate
        framerate_layout = QHBoxLayout()
        framerate_label = QLabel("Target FPS:")
        framerate_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        self.framerate_spinbox = QSpinBox()
        self.framerate_spinbox.setRange(1, 30)
        self.framerate_spinbox.setValue(1)
        self.framerate_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px;
                min-width: 60px;
            }
        """)
        framerate_layout.addWidget(framerate_label)
        framerate_layout.addWidget(self.framerate_spinbox)
        framerate_layout.addStretch()
        layout.addLayout(framerate_layout)

        # Zoom
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        self.zoom_spinbox = QSpinBox()
        self.zoom_spinbox.setRange(25, 400)
        self.zoom_spinbox.setValue(100)
        self.zoom_spinbox.setSuffix("%")
        self.zoom_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px;
                min-width: 60px;
            }
        """)
        zoom_layout.addWidget(zoom_label)
        zoom_layout.addWidget(self.zoom_spinbox)
        zoom_layout.addStretch()
        layout.addLayout(zoom_layout)

        # Analysis toggle
        self.analysis_checkbox = QCheckBox("Enable Preview Analysis")
        self.analysis_checkbox.setChecked(False)
        self.analysis_checkbox.setStyleSheet("color: #ffffff; font-size: 12px;")
        layout.addWidget(self.analysis_checkbox)
        layout.addStretch()

    def setup_connections(self):
        self.aspect_ratio_checkbox.toggled.connect(self.aspect_ratio_changed.emit)
        self.framerate_spinbox.valueChanged.connect(self.framerate_changed.emit)
        self.zoom_spinbox.valueChanged.connect(self._emit_zoom)
        self.analysis_checkbox.toggled.connect(self.analysis_toggled.emit)

    def _emit_zoom(self, value):
        self.zoom_changed.emit(float(value))

    def set_aspect_ratio(self, keep: bool):
        self.aspect_ratio_checkbox.setChecked(keep)

    def set_framerate(self, fps: int):
        self.framerate_spinbox.setValue(fps)

    def set_zoom(self, zoom: float):
        self.zoom_spinbox.setValue(int(zoom))

    def set_analysis(self, enabled: bool):
        self.analysis_checkbox.setChecked(enabled)

    def get_aspect_ratio(self) -> bool:
        return self.aspect_ratio_checkbox.isChecked()

    def get_framerate(self) -> int:
        return self.framerate_spinbox.value()

    def get_zoom(self) -> float:
        return float(self.zoom_spinbox.value())

    def is_analysis_enabled(self) -> bool:
        return self.analysis_checkbox.isChecked() 