from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QSplitter
from PySide6.QtCore import Qt
from gui.widgets.histogram_widget import HistogramGraphWidget, HistogramDataWidget
from gui.widgets.focus_widget import FocusWidget, FocusDataWidget

class AnalysisWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        # Left: Graphs stacked vertically
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.histogram_widget = HistogramGraphWidget(self)
        self.focus_widget = FocusWidget(self)
        left_layout.addWidget(self.histogram_widget)
        left_layout.addWidget(self.focus_widget)
        # Right: Tabs for stats
        self.stats_tabs = QTabWidget()
        self.histogram_data_widget = HistogramDataWidget(self)
        self.stats_tabs.addTab(self.histogram_data_widget, "Histogram Stats")
        self.focus_data_widget = FocusDataWidget(self)
        self.stats_tabs.addTab(self.focus_data_widget, "Focus Stats")
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(self.stats_tabs)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        # Set splitter as the main layout
        layout = QVBoxLayout(self)
        layout.addWidget(splitter)
        self.setLayout(layout)

    def set_histogram(self, histogram):
        self.histogram_widget.set_histogram(histogram)
        self.histogram_data_widget.set_histogram(histogram) 