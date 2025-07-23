from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool
import time
from core.camera.camera_manager import camera_manager, CameraStatus
import logging

logger = logging.getLogger(__name__)

class PreviewTask(QRunnable):
    
    def __init__(self, preview_manager: "PreviewManager"):
        super().__init__()
        self._preview_manager = preview_manager
        
    def run(self):
        """Run the preview task"""
        while True:
            logger.debug(f"Preview task running, framerate: {self._preview_manager.get_framerate()}, live preview active: {self._preview_manager.get_live_preview_active()}")
            if camera_manager.get_status() != CameraStatus.CONNECTED or self._preview_manager.get_framerate() <= 0 or not self._preview_manager.get_live_preview_active():
                time.sleep(1)
                continue
            
            camera_manager.capture_preview()
            sleep_time = (1 / self._preview_manager.get_framerate()) 
            if sleep_time > 0:
                time.sleep(sleep_time)

class PreviewManager(QObject):
    """Manager for preview settings"""
    live_preview_active = Signal(bool)
    aspect_ratio_changed = Signal(bool)
    framerate_changed = Signal(int)
    zoom_changed = Signal(float)

    def __init__(self):
        super().__init__()
        self._aspect_ratio = True
        self._framerate = 1
        self._zoom = 100
        self._analysis = False
        self._live_preview_active = False

        QThreadPool.globalInstance().start(PreviewTask(self))
        
    def set_aspect_ratio(self, aspect_ratio: bool):
        self._aspect_ratio = aspect_ratio
        self.aspect_ratio_changed.emit(aspect_ratio)
    
    def set_framerate(self, framerate: int):
        self._framerate = framerate
        self.framerate_changed.emit(framerate)
        
    def set_zoom(self, zoom: float):
        self._zoom = zoom
        self.zoom_changed.emit(zoom)
        
    def get_aspect_ratio(self) -> bool:
        return self._aspect_ratio
    
    def get_framerate(self) -> int:
        return self._framerate
    
    def get_zoom(self) -> float:
        return self._zoom
    
    def get_analysis(self) -> bool:
        return self._analysis
    
    def set_live_preview_active(self, active: bool):
        self._live_preview_active = active
        self.live_preview_active.emit(active)
        
    def get_live_preview_active(self) -> bool:
        return self._live_preview_active
    
preview_manager = PreviewManager()  