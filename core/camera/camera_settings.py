from dataclasses import dataclass
import gphoto2 as gp
from enum import Enum
from PySide6.QtCore import QObject, Signal
import json
from core.camera.camera_manager import camera_manager
from utils.utils import default_on_exception
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


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
    
    def validate(self):
        for setting in self.settings.keys():
            if setting not in camera_settings.settings:
                raise ValueError(f"Setting {setting} not found in camera_settings")
            if camera_settings.settings[setting].readonly:
                raise ValueError(f"Setting {setting} is readonly")
            if camera_settings.settings[setting].choices and self.settings[setting] not in camera_settings.settings[setting].choices:
                raise ValueError(f"Setting {setting} has invalid value: {self.settings[setting]}")
        return True
    
    def apply(self):
        if not self.validate():
            return False
        camera_manager.set_settings(self.settings)
        return True
        
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


class SettingProfileManager(QObject):
    """Manages camera setting profiles"""
    
    profile_added = Signal(object)  # Signal when profile is added
    profile_removed = Signal(str)   # Signal when profile is removed
    profile_updated = Signal(object)  # Signal when profile is updated
    
    def __init__(self):
        super().__init__()
        self._profiles: Dict[str, SettingProfile] = {}
        self._profiles_file = Path("./data/config/setting_profiles.json")
        self.load_profiles()
        
    def load_profiles(self):
        """Load profiles from file"""
        try:
            if self._profiles_file.exists():
                with open(self._profiles_file, 'r') as f:
                    profiles_data = json.load(f)
                    
                for profile_data in profiles_data:
                    try:
                        profile = SettingProfile.from_dict(profile_data)
                        self._profiles[profile.name] = profile
                    except Exception as e:
                        logger.error(f"Failed to load profile {profile_data.get('name', 'unknown')}: {e}")
                        
                logger.info(f"Loaded {len(self._profiles)} setting profiles")
            else:
                logger.info("No profiles file found, starting with empty profile list")
                
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")
            
    def save_profiles(self):
        """Save profiles to file"""
        try:
            self._profiles_file.parent.mkdir(parents=True, exist_ok=True)
            
            profiles_data = [profile.as_dict() for profile in self._profiles.values()]
            
            with open(self._profiles_file, 'w') as f:
                json.dump(profiles_data, f, indent=4)
                
            logger.info(f"Saved {len(self._profiles)} setting profiles")
            
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
    
    def get_profiles(self) -> List[SettingProfile]:
        """Get all profiles"""
        return list(self._profiles.values())
        
    def get_profile(self, name: str) -> Optional[SettingProfile]:
        """Get profile by name"""
        return self._profiles.get(name)
        
    def add_profile(self, profile: SettingProfile) -> bool:
        """Add a new profile"""           
        self._profiles[profile.name] = profile
        self.save_profiles()
        self.profile_added.emit(profile)
        logger.info(f"Added profile: {profile.name}")
        return True
        
    def remove_profile(self, name: str) -> bool:
        """Remove a profile"""
        if name not in self._profiles:
            logger.warning(f"Profile '{name}' not found")
            return False
            
        del self._profiles[name]
        self.save_profiles()
        self.profile_removed.emit(name)
        logger.info(f"Removed profile: {name}")
        return True
        
    def update_profile(self, name: str, **kwargs) -> bool:
        """Update profile properties"""
        profile = self._profiles.get(name)
        if not profile:
            return False
            
        # Create updated profile with new values
        new_settings = profile.settings.copy()
        if 'settings' in kwargs:
            new_settings.update(kwargs['settings'])
            
        new_name = kwargs.get('name', name)
        
        # Remove old profile and add updated one
        del self._profiles[name]
        updated_profile = SettingProfile(name=new_name, settings=new_settings)
        self._profiles[new_name] = updated_profile
        
        self.save_profiles()
        self.profile_updated.emit(updated_profile)
        logger.info(f"Updated profile: {updated_profile.name}")
        return True
        
class CameraSettings(QObject):
    settings: dict[str, CameraSetting]
    
    def __init__(self):
        super().__init__()
        self.settings = self._load_from_file(Path("./data/config/camera_settings.json"))
    
    def _load_from_file(self, file_path: Path):
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        with open(file_path, "r") as f:
            return {setting["name"]: CameraSetting.from_dict(setting) for setting in json.load(f)}
    
        
    def get_setting(self, name: str):
        return self.settings.get(name)
    
    def get_settings(self):
        return self.settings.values()

# Global instances
camera_settings = CameraSettings()
settings_profiles = SettingProfileManager()

# Create default profile if it doesn't exist
default_profile = settings_profiles.get_profile("Default")
if not default_profile:
    # Create a basic default profile
    default_profile = SettingProfile(
        name="Default",
        settings={
            "aperture": "5.6",
            "shutterspeed": "1/125",
            "iso": "1600",
            "imageformat": "RAW + L",
            "highisonr": "High",
            "picturestyle": "Neutral",
            "colortemperature": "5200",
            "whitebalance": "Daylight",
            "colorspace": "AdobeRGB"
        }
    )
    settings_profiles.add_profile(default_profile)

