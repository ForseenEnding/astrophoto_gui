from gphoto2 import gphoto2 as gp
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from PySide6.QtCore import QObject, Signal, Slot, QRunnable
from pathlib import Path
import logging
import numpy as np
from PIL import Image
import io
import uuid
from threading import RLock

logger = logging.getLogger(__name__)

camera = None

class CameraStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class CameraStatusChangedEvent:
    status: CameraStatus
    error_message: Optional[str] = None
    timestamp: datetime = datetime.now()
    
@dataclass
class CameraImageCapturedEvent:
    image_id: str
    image_paths: List[str]
    timestamp: datetime = datetime.now()
    
@dataclass
class PreviewImageCapturedEvent:
    image_id: str
    image_data: bytes
    timestamp: datetime = datetime.now()
    
    
@dataclass
class SettingsChangedEvent:
    settings: Dict[str, str]
    timestamp: datetime = datetime.now()
    

class CameraManager(QObject):
    # Signals
    camera_status_changed = Signal(CameraStatusChangedEvent)  # CameraStatusChangedEvent
    image_captured = Signal(CameraImageCapturedEvent)  # CameraImageCapturedEvent
    preview_image_captured = Signal(PreviewImageCapturedEvent)  # PreviewImageCapturedEvent
    settings_changed = Signal(SettingsChangedEvent)  # SettingsChangedEvent
    
    def __init__(self):
        super().__init__()
        self.camera = gp.Camera()
        self._status = CameraStatus.DISCONNECTED
        self._current_settings = {}
        self._lock = RLock()
        
    def connect(self):
        """Connect to the camera"""
        try:
            with self._lock:
                self.camera.init()
            self._status = CameraStatus.CONNECTED
            self._emit_status_changed()
            logger.info("Camera connected successfully")
        except Exception as e:
            self._status = CameraStatus.ERROR
            self._emit_status_changed(error_message=str(e))
            logger.error(f"Failed to connect to camera: {e}")
            raise
        
    def disconnect(self):
        """Disconnect from the camera"""
        try:
            with self._lock:
                self.camera.exit()
            self._status = CameraStatus.DISCONNECTED
            self._emit_status_changed()
            logger.info("Camera disconnected successfully")
        except Exception as e:
            self._status = CameraStatus.ERROR
            self._emit_status_changed(error_message=str(e))
            logger.error(f"Failed to disconnect from camera: {e}")
            raise
        
    def get_status(self) -> CameraStatus:
        """Get current camera status"""
        return self._status
        
    def get_camera(self):
        """Get the gphoto2 camera object"""
        return self.camera
    
    def get_config(self):
        """Get camera configuration"""
        if self._status != CameraStatus.CONNECTED:
            raise RuntimeError("Camera not connected")
        return self.camera.get_config()

    def get_settings(self, setting_names: List[str]) -> Dict[str, str]:
        """Get current camera settings"""
        if self._status != CameraStatus.CONNECTED:
            raise RuntimeError("Camera not connected")
        
        with self._lock:
            try:
                config = self.camera.get_config()
                settings = {}
                
                for name in setting_names:
                    child = config.get_child_by_name(name)
                    if child:
                        settings[name] = child.get_value()
                    else:
                        logger.warning(f"Setting {name} not found") 
                self._current_settings = settings
                return settings
                
            except Exception as e:
                logger.error(f"Failed to get camera settings: {e}")
                raise
    
    def set_settings(self, settings: Dict[str, str]):
        """Set camera settings"""

        if self._status != CameraStatus.CONNECTED:
            raise RuntimeError("Camera not connected")
         
        with self._lock:
            try:
                config = self.camera.get_config()
                changed_settings = {}
                
                for name, value in settings.items():
                    try:
                        child = config.get_child_by_name(name)
                        if child is not None:
                            old_value = child.get_value()
                            child.set_value(value)
                            changed_settings[name] = value
                            logger.debug(f"Set {name} = {value}")
                    except Exception as e:
                        logger.warning(f"Failed to set setting {name}: {e}")
                
                if changed_settings:
                    self.camera.set_config(config)
                    self._current_settings.update(changed_settings)
                    self._emit_settings_changed(changed_settings)
                    logger.info(f"Updated camera settings: {list(changed_settings.keys())}")
                    
            except Exception as e:
                logger.error(f"Failed to set camera settings: {e}")
                raise
    
    def capture_image(self, save_path: Path) -> List[str]:
        """Capture an image and save it to the specified path"""
        if self._status != CameraStatus.CONNECTED:
            raise RuntimeError("Camera not connected")
        
        with self._lock:
            try:
                # Ensure directory exists
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                captured_files = []
                # Capture image
                file_path = self.camera.capture(gp.GP_CAPTURE_IMAGE)
                captured_files.append(file_path)
                
                # Wait for additional files (dual capture mode)
                while True:
                    logger.debug("Waiting for additional files")
                    event, data = self.camera.wait_for_event(100)
                    if event == gp.GP_EVENT_CAPTURE_COMPLETE or event == gp.GP_EVENT_TIMEOUT:
                        break
                    elif event == gp.GP_EVENT_FILE_ADDED:
                        captured_files.append(data)
                
                result = []
                for file_path in captured_files:
                    # Download file
                    camera_file = self.camera.file_get(
                        file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL
                    )
                    
                    # Save file
                    file_extension = file_path.name.split(".")[-1]
                    final_path = save_path.with_suffix(f".{file_extension}")
                    camera_file.save(str(final_path))
                    result.append(str(final_path))
                    
                    # Delete file from camera
                    self.camera.file_delete(file_path.folder, file_path.name)
                    
                    logger.info(f"Captured image: {final_path}")

                self._emit_image_captured(result)
                
                return result
                
            except Exception as e:
                logger.error(f"Failed to capture image: {e}")
                raise
    
    def capture_preview(self) -> bytes:
        """Capture a preview image"""
        if self._status != CameraStatus.CONNECTED:
            raise RuntimeError("Camera not connected")
        
        with self._lock:
            try:
                # Capture preview
                preview_data = self.camera.capture_preview()
                
                # Get preview file
                preview_file = preview_data.get_data_and_size().tobytes()
                
                self._emit_preview_captured(preview_file)
                logger.debug("Captured preview image")
                
                return preview_file
                
            except Exception as e:                
                logger.error(f"Failed to capture preview: {e}")
                raise
    
    def _emit_status_changed(self, error_message: Optional[str] = None):
        """Emit camera status changed signal"""
        logger.debug(f"Camera status changed to {self._status}")
        event = CameraStatusChangedEvent(
            status=self._status,
            error_message=error_message
        )
        self.camera_status_changed.emit(event)
    
    def _emit_image_captured(self, image_paths: List[str]):
        """Emit image captured signal"""
        image_id = str(uuid.uuid4())
        event = CameraImageCapturedEvent(image_id=image_id, image_paths=image_paths)
        self.image_captured.emit(event)
    
    def _emit_preview_captured(self, image_data: bytes):
        """Emit preview image captured signal"""
        image_id = str(uuid.uuid4())
        event = PreviewImageCapturedEvent(image_id=image_id, image_data=image_data)
        self.preview_image_captured.emit(event)
    
    def _emit_settings_changed(self, settings: Dict[str, str]):
        """Emit settings changed signal"""
        logger.debug(f"Settings changed: {settings}")
        event = SettingsChangedEvent(settings=settings)
        self.settings_changed.emit(event)
        
        

# Global camera controller instance
camera_manager = CameraManager()