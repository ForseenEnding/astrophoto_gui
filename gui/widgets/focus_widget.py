from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen
from core.analysis.focus import focus_manager, FocusResult

class FocusGraphWidget(QWidget):
    def __init__(self, focus_scores_ref, max_points, parent=None):
        super().__init__(parent)
        self._focus_scores_ref = focus_scores_ref
        self._max_points = max_points
        self.setMinimumHeight(100)

    def paintEvent(self, event):
        super().paintEvent(event)
        focus_scores = self._focus_scores_ref()
        if not focus_scores:
            return
        painter = QPainter(self)
        width = self.width()
        height = self.height()
        n = len(focus_scores)
        if n < 2:
            painter.end()
            return
        max_focus = max(focus_scores)
        min_focus = min(focus_scores)
        focus_range = max_focus - min_focus if max_focus != min_focus else 1
        # Draw axes
        painter.setPen(QPen(QColor(180, 180, 180), 1, Qt.DashLine))
        painter.drawLine(0, height - 1, width, height - 1)  # X axis
        painter.drawLine(0, 0, 0, height)  # Y axis
        # Draw focus line
        painter.setPen(QPen(QColor(0, 180, 255), 2))
        x_step = width / (self._max_points - 1)
        points = []
        for i, score in enumerate(focus_scores):
            x = int(i * x_step)
            y = int(height - ((score - min_focus) / focus_range) * height)
            points.append((x, y))
        for i in range(1, len(points)):
            painter.drawLine(points[i-1][0], points[i-1][1], points[i][0], points[i][1])
        painter.end()

class FocusDataWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._focus_result = None
        self._enabled = False
        self.label = QLabel(self)
        self.enable_checkbox = QCheckBox("Enable Focus Analysis", self)
        self.enable_checkbox.setChecked(self._enabled)
        self.enable_checkbox.stateChanged.connect(self.toggle_enabled)
        self.reset_button = QPushButton("Reset", self)
        self.reset_button.clicked.connect(self.reset)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.enable_checkbox)
        layout.addStretch(1)
        layout.addWidget(self.reset_button)
        self.setLayout(layout)
        focus_manager.focus_completed.connect(self.on_focus_completed)
        self.update_label()

    def on_focus_completed(self, result: FocusResult):
        self._focus_result = result
        self.update_label()

    def update_label(self):
        if self._focus_result:
            text = f"Image ID: {self._focus_result.image_id}\nFocus Score: {self._focus_result.focus_score:.2f}\nTime: {self._focus_result.timestamp.strftime('%H:%M:%S')}"
        else:
            text = "No focus data yet."
        self.label.setText(text)

    def toggle_enabled(self, state):
        self._enabled = bool(state)
        focus_manager.set_enabled(self._enabled)

    def reset(self):
        # This will clear the scores in the parent FocusWidget if accessible
        parent = self.parent()
        if parent and hasattr(parent, '_focus_scores'):
            parent._focus_scores.clear()
            if hasattr(parent, 'graph_widget'):
                parent.graph_widget.update()

class FocusWidget(QWidget):
    def __init__(self, parent=None, max_points=50):
        super().__init__(parent)
        self._focus_scores = []
        self._max_points = max_points
        self._init_ui()
        focus_manager.focus_completed.connect(self.on_focus_completed)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        # Graph widget
        self.graph_widget = FocusGraphWidget(lambda: self._focus_scores, self._max_points, self)
        layout.addWidget(self.graph_widget)
        self.setLayout(layout)

    def on_focus_completed(self, result: FocusResult):
        self._focus_scores.append(result.focus_score)
        if len(self._focus_scores) > self._max_points:
            self._focus_scores.pop(0)
        self.graph_widget.update() 