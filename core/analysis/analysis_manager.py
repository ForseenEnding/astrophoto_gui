from dataclasses import dataclass
from PySide6.QtCore import QRunnable, QThreadPool, Slot, QObject, Signal
from pathlib import Path
import numpy as np
from PIL import Image
import logging
from datetime import datetime
from .focus import detect_focus
from .histogram import compute_histogram, Histogram
from core.camera.camera_manager import camera_manager, CameraImageCapturedEvent, PreviewImageCapturedEvent
import io

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResultEvent(QObject):
    focus_score: float
    histogram: Histogram
    timestamp: datetime
    
    def __init__(self, focus_score: float, histogram: Histogram):
        super().__init__()
        self.focus_score = focus_score
        self.histogram = histogram
        self.timestamp = datetime.now()

@dataclass
class AnalysisTask(QRunnable):
    
    def __init__(self, image: bytes | Path, result_signal: Signal):
        super().__init__()
        self._target_image = image
        self._result_signal = result_signal
        
    @Slot()
    def run(self):
        """Run the analysis task"""
        if isinstance(self._target_image, bytes):
            pil_image = Image.open(io.BytesIO(self._target_image))
        else:
            pil_image = Image.open(self._target_image)
            
        rgb_array = np.array(pil_image.convert("RGB"))
        focus_score = detect_focus(rgb_array)
        logger.info(f"Focus score: {focus_score}")
        histogram = compute_histogram(rgb_array)

        
        self._emit_analysis_result(focus_score, histogram)
        
    def _emit_analysis_result(self, focus_score: float, histogram: Histogram):
        """Emit analysis result signal"""
        event = AnalysisResultEvent(focus_score=focus_score, histogram=histogram)   
        self._result_signal.emit(event)
        
class AnalysisManager(QObject):
    analysis_result = Signal(AnalysisResultEvent)
    
    preview_analysis_active = Signal(bool)
    image_analysis_active = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self._analyze_preview = False
        self._analyze_image = False
        
        camera_manager.image_captured.connect(self._on_image_captured)
        camera_manager.preview_image_captured.connect(self._on_preview_image_captured)
        
    def _on_image_captured(self, event: CameraImageCapturedEvent):
        if self._analyze_image:
            for image_path in event.image_paths:
                if image_path.endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif')):
                    self.analyze(image_path)
                else:
                    logger.debug(f"Skipping analysis of {image_path} because it is not a supported image format")
            
    def _on_preview_image_captured(self, event: PreviewImageCapturedEvent):
        if self._analyze_preview:
            self.analyze(event.image_data)
        
    def analyze(self, image: bytes | Path):
        QThreadPool.globalInstance().start(AnalysisTask(image, self.analysis_result))
        
    def analyze_previews(self, enabled: bool):
        self._analyze_preview = enabled
        self.preview_analysis_active.emit(enabled)
        
    def analyze_images(self, enabled: bool):
        self._analyze_image = enabled
        self.image_analysis_active.emit(enabled)
        
    def is_preview_analysis_active(self) -> bool:
        return self._analyze_preview
    
    def is_image_analysis_active(self) -> bool:
        return self._analyze_image

    
analysis_manager = AnalysisManager()