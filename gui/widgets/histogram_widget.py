from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QCheckBox, QHBoxLayout, QLabel, QGridLayout, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen
from core.analysis.histogram import histogram_manager, Histogram

class HistogramGraphWidget(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._histogram = None
        self._channels = histogram_manager.get_channels()
        histogram_manager.histogram_completed.connect(self.on_histogram_completed)
        histogram_manager.channels_changed.connect(self.on_channels_changed)
        self.setMinimumHeight(100)

    def set_histogram(self, histogram: Histogram):
        self._histogram = histogram
        self.update()

    def on_channels_changed(self, channels):
        self._channels = channels
        self.update()

    def on_histogram_completed(self, histogram: Histogram):
        self.set_histogram(histogram)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._histogram:
            return
        painter = QPainter(self)
        width = self.width()
        height = self.height()
        bins = len(self._histogram.r.hist)
        max_count = 1
        if self._channels['r']:
            max_count = max(max_count, max(self._histogram.r.hist))
        if self._channels['g']:
            max_count = max(max_count, max(self._histogram.g.hist))
        if self._channels['b']:
            max_count = max(max_count, max(self._histogram.b.hist))
        if self._channels['luminance']:
            max_count = max(max_count, max(self._histogram.luminance.hist))
        bar_width = width / bins
        for i in range(bins):
            if self._channels['r']:
                value = self._histogram.r.hist[i]
                bar_height = int((value / max_count) * height)
                painter.setPen(QPen(QColor(255,0,0), 1))
                painter.drawLine(
                    int(i * bar_width), height,
                    int(i * bar_width), height - bar_height
                )
            if self._channels['g']:
                value = self._histogram.g.hist[i]
                bar_height = int((value / max_count) * height)
                painter.setPen(QPen(QColor(0,255,0), 1))
                painter.drawLine(
                    int(i * bar_width), height,
                    int(i * bar_width), height - bar_height
                )
            if self._channels['b']:
                value = self._histogram.b.hist[i]
                bar_height = int((value / max_count) * height)
                painter.setPen(QPen(QColor(0,0,255), 1))
                painter.drawLine(
                    int(i * bar_width), height,
                    int(i * bar_width), height - bar_height
                )
        if self._channels['luminance']:
            for i in range(bins):
                value = self._histogram.luminance.hist[i]
                bar_height = int((value / max_count) * height)
                painter.setPen(QPen(QColor(220,220,220), 1))
                painter.drawLine(
                    int(i * bar_width), height,
                    int(i * bar_width), height - bar_height
                )
        painter.end() 

class HistogramDataWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._histogram = None
        self._enabled = False
        histogram_manager.histogram_completed.connect(self.on_histogram_completed)
        histogram_manager.channels_changed.connect(self.on_channels_changed)
        self.setMinimumHeight(100)
        self._stat_lines = []
        self.r_checkbox = QCheckBox("R", self)
        self.g_checkbox = QCheckBox("G", self)
        self.b_checkbox = QCheckBox("B", self)
        self.luminance_checkbox = QCheckBox("Luminance", self)
        self.r_checkbox.setChecked(histogram_manager.get_channels()['r'])
        self.g_checkbox.setChecked(histogram_manager.get_channels()['g'])
        self.b_checkbox.setChecked(histogram_manager.get_channels()['b'])
        self.luminance_checkbox.setChecked(histogram_manager.get_channels()['luminance'])
        self.r_checkbox.stateChanged.connect(lambda state: histogram_manager.set_channel_enabled('r', bool(state)))
        self.g_checkbox.stateChanged.connect(lambda state: histogram_manager.set_channel_enabled('g', bool(state)))
        self.b_checkbox.stateChanged.connect(lambda state: histogram_manager.set_channel_enabled('b', bool(state)))
        self.luminance_checkbox.stateChanged.connect(lambda state: histogram_manager.set_channel_enabled('luminance', bool(state)))
        self.enable_checkbox = QCheckBox("Enable Histogram Analysis", self)
        self.enable_checkbox.setChecked(self._enabled)
        self.enable_checkbox.stateChanged.connect(self.toggle_enabled)
        self.reset_button = QPushButton("Reset", self)
        self.reset_button.clicked.connect(self.reset)
        layout = QVBoxLayout(self)
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(QLabel("Channels:"))
        channel_layout.addWidget(self.r_checkbox)
        channel_layout.addWidget(self.g_checkbox)
        channel_layout.addWidget(self.b_checkbox)
        channel_layout.addWidget(self.luminance_checkbox)
        layout.addLayout(channel_layout)
        self.stats_grid = QGridLayout()
        layout.addLayout(self.stats_grid)
        layout.addStretch(1)
        layout.addWidget(self.enable_checkbox)
        layout.addWidget(self.reset_button)
        self.setLayout(layout)
        self.update_stats_columns()

    def set_histogram(self, histogram: Histogram):
        self._histogram = histogram
        self.update_stats_columns()
        self.update()

    def on_histogram_completed(self, histogram: Histogram):
        self.set_histogram(histogram)

    def on_channels_changed(self, channels):
        self.r_checkbox.setChecked(channels['r'])
        self.g_checkbox.setChecked(channels['g'])
        self.b_checkbox.setChecked(channels['b'])
        self.luminance_checkbox.setChecked(channels['luminance'])
        self.update_stats_columns()

    def update_stats_columns(self):
        while self.stats_grid.count():
            item = self.stats_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if not self._histogram:
            return
        channels = histogram_manager.get_channels()
        columns = []
        if channels['r']:
            columns.append(('R', self._histogram.r, QColor(255,0,0)))
        if channels['g']:
            columns.append(('G', self._histogram.g, QColor(0,255,0)))
        if channels['b']:
            columns.append(('B', self._histogram.b, QColor(0,0,255)))
        if channels['luminance']:
            columns.append(('Luminance', self._histogram.luminance, QColor(220,220,220)))
        for col, (name, stats, color) in enumerate(columns):
            header = QLabel(f"<b>{name}</b>")
            header.setStyleSheet(f"color: rgb({color.red()},{color.green()},{color.blue()})")
            self.stats_grid.addWidget(header, 0, col, alignment=Qt.AlignHCenter)
            stat_lines = [
                f"Mean: {stats.mean:.1f}",
                f"Median: {stats.median:.1f}",
                f"Std: {stats.std:.1f}",
                f"Black Point: {stats.black_point}",
                f"White Point: {stats.white_point}",
                f"Mode: {stats.mode}",
                f"Clipped Left: {'Yes' if stats.clipped_left else 'No'}",
                f"Clipped Right: {'Yes' if stats.clipped_right else 'No'}",
            ]
            for row, line in enumerate(stat_lines, 1):
                label = QLabel(line)
                label.setStyleSheet(f"color: rgb({color.red()},{color.green()},{color.blue()})")
                label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                self.stats_grid.addWidget(label, row, col, alignment=Qt.AlignLeft)

    def paintEvent(self, event):
        super().paintEvent(event)
        # No longer draw stats here; handled by stats_grid

    def toggle_enabled(self, state):
        self._enabled = bool(state)
        histogram_manager.set_enabled(self._enabled)

    def reset(self):
        # No direct access to histogram data to reset, but you can add logic if needed
        pass