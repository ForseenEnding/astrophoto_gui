from dataclasses import dataclass
from xxlimited import Str
from PySide6.QtCore import QRunnable, QThreadPool, Slot, QObject, Signal
from pathlib import Path
import numpy as np
from PIL import Image
import logging
from datetime import date, datetime, timezone
from core.camera.camera_manager import camera_manager, CameraImageCapturedEvent, PreviewImageCapturedEvent
import io
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class AreaOfInterest:
    x: int
    y: int
    width: int
    height: int    

@dataclass
class ImageReadyEvent():
    rgb: np.ndarray
    image_id: str
    timestamp: datetime
    aoi: Optional[AreaOfInterest] = None
    
    def __init__(self, rgb: np.ndarray, image_id: Str, aoi: Optional[AreaOfInterest] = None):
        self.rgb = rgb
        self.image_id = image_id
        self.timestamp = datetime.now(timezone.utc)
        self.aoi = aoi
        
class AnalysisManager(QObject):
    image_ready = Signal(ImageReadyEvent)
    
    def __init__(self):
        super().__init__()       
        camera_manager.image_captured.connect(self._on_image_captured)
        camera_manager.preview_image_captured.connect(self._on_preview_image_captured)
        self._aoi: Optional[AreaOfInterest] = None
    
    def set_aoi(self, aoi: Optional[AreaOfInterest]):
        self._aoi = aoi
    
    def get_aoi(self) -> Optional[AreaOfInterest]:
        return self._aoi
    
    def _on_image_captured(self, event: CameraImageCapturedEvent):
        for image_path in event.image_paths:
            extension = image_path.split('.')[-1].lower()
            if extension in ('.jpg', '.jpeg', '.png', '.tiff', '.tif'):
                self._emit_image_ready(event.image_id, image_path)
            else:
                logger.debug(f"Skipping analysis of {image_path} because it is not a supported image format")
            
    def _on_preview_image_captured(self, event: PreviewImageCapturedEvent):
        self._emit_image_ready(event.image_id, event.image_data)
        
    def _emit_image_ready(self, image_id: str, image: bytes | Path):
        if isinstance(image, bytes):
            pil_image = Image.open(io.BytesIO(image))
        else:
            pil_image = Image.open(image)
            
        rgb_array = np.array(pil_image.convert("RGB"))
        aoi = self._aoi
        if aoi:
            x, y, w, h = aoi.x, aoi.y, aoi.width, aoi.height
            rgb_array = rgb_array[y:y+h, x:x+w]
        self.image_ready.emit(ImageReadyEvent(rgb_array, image_id, aoi=aoi))

    
analysis_manager = AnalysisManager()