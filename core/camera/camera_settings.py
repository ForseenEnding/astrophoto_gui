from dataclasses import dataclass
import gphoto2 as gp
from enum import Enum
from PySide6.QtCore import QObject, Signal
import json
from core.camera.camera_controller import camera_controller
from utils.utils import default_on_exception
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class Category(Enum):
    CAMERA_INFO = "camera_info"
    ACTIONS = "actions"
    CAMERA_SETTINGS = "settings"
    STATUS = "status"
    IMAGE_SETTINGS = "image_settings"
    CAPTURE_SETTINGS = "capture_settings"
    OTHER = "other"

class Type(Enum):
    SECTION = "section"
    RADIO = "radio"
    TEXT = "text"
    TOGGLE = "toggle"
    MENU = "menu"
    DATE = "date"
    
    @staticmethod
    def from_string(type_str: str) -> "Type":
        return Type(type_str)
    
    @staticmethod
    def from_index(index: int) -> "Type":
        match index:
            case gp.GP_WIDGET_SECTION:
                return Type.SECTION
            case gp.GP_WIDGET_RADIO:
                return Type.RADIO
            case gp.GP_WIDGET_TEXT:
                return Type.TEXT
            case gp.GP_WIDGET_TOGGLE:
                return Type.TOGGLE
            case gp.GP_WIDGET_MENU:
                return Type.MENU
            case gp.GP_WIDGET_DATE:
                return Type.DATE
            case _:
                raise ValueError(f"Invalid type index: {index}")

@dataclass(frozen=True)
class CameraSetting:
    name: str
    type: Type
    label: str
    readonly: bool
    default_value: str
    choices: list[str]
        
    def as_dict(self):
        return {
            "name": self.name,
            "type": self.type.value,
            "label": self.label,
            "readonly": self.readonly,
            "default_value": self.default_value,
            "choices": self.choices
        }
    
    @staticmethod
    def from_dict(dict: dict):
        return CameraSetting(
            name=dict["name"],
            type=Type.from_string(dict["type"]),
            label=dict["label"],
            readonly=dict["readonly"],
            default_value=dict["default_value"],
            choices=dict["choices"])
    
    
@dataclass(frozen=True)
class SettingChangedEvent:
    setting: CameraSetting
    old_value: str
    new_value: str
    timestamp: datetime = datetime.now()
    
@dataclass(frozen=True)
class SettingProfile:
    name: str
    settings: dict[str, str]
        
    def as_dict(self):
        return {
            "name": self.name,
            "settings": self.settings
        }
    
    @staticmethod
    def from_dict(data: dict) -> "SettingProfile":
        return SettingProfile(
            name=data["name"],
            settings=data["settings"]  # Already in correct format
        )
        
class CameraSettings(QObject):
    settings: dict[str, CameraSetting]
    
    def __init__(self):
        super().__init__()
        self.settings = self._load_from_file(Path("./config/camera_settings.json"))
    
    def _load_from_file(self, file_path: Path):
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        with open(file_path, "r") as f:
            return {setting["name"]: CameraSetting.from_dict(setting) for setting in json.load(f)}
    
        
    def get_setting(self, name: str):
        return self.settings.get(name)
    
    def get_settings(self):
        return self.settings.values()

camera_settings = CameraSettings()

if __name__ == "__main__":
    with open ("./config/setting_profiles.json", "w") as f:
        profile = SettingProfile(
            name="test",
            settings={
                "iso": "100",
                "aperture": "f/2.8",
                "shutter_speed": "1/1000"
            }
        )
        json.dump(profile.as_dict(), f, indent=4)
    print(camera_settings.get_setting("iso"))
