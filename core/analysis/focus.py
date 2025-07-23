from dataclasses import dataclass
from typing import Optional
import numpy as np
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from core.analysis.analysis_manager import analysis_manager, ImageReadyEvent, AreaOfInterest
from datetime import datetime, timezone

def detect_focus(
    rgb: np.ndarray,
    area_of_interest: Optional[AreaOfInterest] = None
) -> float:
    """
    Compute a simple focus metric (variance of Laplacian) for a RGB image.
    Optionally, restrict to an area of interest: (x, y, width, height).
    Returns a single float value (higher means sharper focus).
    """
    # Convert to grayscale
    gray = np.dot(rgb[...,:3], [0.2989, 0.5870, 0.1140])

    # Crop to area of interest if specified
    if area_of_interest:
        x, y, w, h = area_of_interest.x, area_of_interest.y, area_of_interest.width, area_of_interest.height
        gray = gray[y:y+h, x:x+w]

    # Compute Laplacian (simple kernel)
    laplacian = (
        -4 * gray +
        np.roll(gray, 1, axis=0) + np.roll(gray, -1, axis=0) +
        np.roll(gray, 1, axis=1) + np.roll(gray, -1, axis=1)
    )
    focus_metric = np.var(laplacian)
    return float(focus_metric)

@dataclass
class FocusResult:
    image_id: str
    focus_score: float
    timestamp: datetime

class FocusWorker(QRunnable):
    def __init__(self, event: ImageReadyEvent, result_signal: Signal, area_of_interest: Optional[AreaOfInterest] = None):
        super().__init__()
        self.event = event
        self.rgb = event.rgb
        self.result_signal = result_signal
        # Use event AOI if present, else fallback
        self.area_of_interest = event.aoi if hasattr(event, 'aoi') and event.aoi is not None else area_of_interest
    def run(self):
        focus_score = detect_focus(self.rgb, self.area_of_interest)
        result = FocusResult(
            image_id=self.event.image_id,
            focus_score=focus_score,
            timestamp=self.event.timestamp
        )
        self.result_signal.emit(result)

class FocusManager(QObject):
    focus_completed = Signal(FocusResult)

    def __init__(self):
        super().__init__()
        self._enabled = False
        self._area_of_interest = None  # Can be set externally if needed
        analysis_manager.image_ready.connect(self._on_image_ready)

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

    def set_area_of_interest(self, area: Optional[AreaOfInterest]):
        self._area_of_interest = area

    def _on_image_ready(self, event: ImageReadyEvent):
        if not self._enabled:
            return
        QThreadPool.globalInstance().start(
            FocusWorker(event, self.focus_completed, self._area_of_interest)
        )

focus_manager = FocusManager() 