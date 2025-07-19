from gphoto2 import gphoto2 as gp
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from PySide6.QtCore import QObject, Signal

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
    image_path: list[str]
    timestamp: datetime = datetime.now()
    
@dataclass
class PreviewImageCapturedEvent:
    image_data: bytes
    timestamp: datetime = datetime.now()
    

class CameraController(QObject):
    
    def __init__(self):
        super().__init__()
        self.camera = gp.Camera()
        
    def connect(self):
        self.camera.init()
        
    def disconnect(self):
        self.camera.exit()
        
    def get_camera(self):
        return self.camera
    
    def get_config(self):
        return self.camera.get_config()

camera_controller = CameraController()