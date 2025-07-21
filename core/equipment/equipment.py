from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Telescope:
    """Represents a telescope"""
    name: str
    focal_length: float  # in mm
    aperture: float      # in mm
    
    @property
    def focal_ratio(self) -> float:
        """Calculate focal ratio (f/stop)"""
        return self.focal_length / self.aperture if self.aperture > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert telescope to dictionary for serialization"""
        return {
            "name": self.name,
            "focal_length": self.focal_length,
            "aperture": self.aperture
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Telescope':
        """Create telescope from dictionary"""
        return cls(
            name=data["name"],
            focal_length=data["focal_length"],
            aperture=data["aperture"]
        )


@dataclass
class Camera:
    """Represents a camera"""
    name: str
    sensor_width: float   # in mm
    sensor_height: float  # in mm
    pixel_size: float     # in microns
    pixel_width: int      # number of pixels
    pixel_height: int     # number of pixels
    diffraction_limit: float  # in arcseconds
    
    @property
    def total_pixels(self) -> int:
        """Calculate total number of pixels"""
        return self.pixel_width * self.pixel_height
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert camera to dictionary for serialization"""
        return {
            "name": self.name,
            "sensor_width": self.sensor_width,
            "sensor_height": self.sensor_height,
            "pixel_size": self.pixel_size,
            "pixel_width": self.pixel_width,
            "pixel_height": self.pixel_height,
            "diffraction_limit": self.diffraction_limit
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Camera':
        """Create camera from dictionary"""
        return cls(
            name=data["name"],
            sensor_width=data["sensor_width"],
            sensor_height=data["sensor_height"],
            pixel_size=data["pixel_size"],
            pixel_width=data["pixel_width"],
            pixel_height=data["pixel_height"],
            diffraction_limit=data["diffraction_limit"]
        )


class EquipmentManager(QObject):
    """Manages telescopes and cameras"""
    
    equipment_updated = Signal()  # Signal when equipment is modified
    
    def __init__(self):
        super().__init__()
        self._telescopes: Dict[str, Telescope] = {}
        self._cameras: Dict[str, Camera] = {}
        self._equipment_file = Path("./data/config/equipment.json")
        self.load_equipment()
        
    def load_equipment(self):
        """Load equipment from file"""
        try:
            if self._equipment_file.exists():
                with open(self._equipment_file, 'r') as f:
                    data = json.load(f)
                    
                # Load telescopes
                for telescope_data in data.get("telescopes", []):
                    try:
                        telescope = Telescope.from_dict(telescope_data)
                        self._telescopes[telescope.name] = telescope
                    except Exception as e:
                        logger.error(f"Failed to load telescope {telescope_data.get('name', 'unknown')}: {e}")
                
                # Load cameras
                for camera_data in data.get("cameras", []):
                    try:
                        camera = Camera.from_dict(camera_data)
                        self._cameras[camera.name] = camera
                    except Exception as e:
                        logger.error(f"Failed to load camera {camera_data.get('name', 'unknown')}: {e}")
                        
                logger.info(f"Loaded {len(self._telescopes)} telescopes and {len(self._cameras)} cameras")
            else:
                logger.info("No equipment file found, starting with empty equipment list")
                
        except Exception as e:
            logger.error(f"Failed to load equipment: {e}")
            
    def save_equipment(self):
        """Save equipment to file"""
        try:
            self._equipment_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "telescopes": [telescope.to_dict() for telescope in self._telescopes.values()],
                "cameras": [camera.to_dict() for camera in self._cameras.values()]
            }
            
            with open(self._equipment_file, 'w') as f:
                json.dump(data, f, indent=4)
                
            logger.info(f"Saved {len(self._telescopes)} telescopes and {len(self._cameras)} cameras")
            
        except Exception as e:
            logger.error(f"Failed to save equipment: {e}")
    
    # Telescope methods
    def add_telescope(self, telescope: Telescope):
        """Add a new telescope"""
        self._telescopes[telescope.name] = telescope
        self.save_equipment()
        self.equipment_updated.emit()
        logger.info(f"Added telescope: {telescope.name}")
        
    def get_telescope(self, name: str) -> Optional[Telescope]:
        """Get telescope by name"""
        return self._telescopes.get(name)
        
    def get_all_telescopes(self) -> List[Telescope]:
        """Get all telescopes"""
        return list(self._telescopes.values())
        
    def update_telescope(self, old_name: str, **kwargs) -> bool:
        """Update telescope properties"""
        telescope = self._telescopes.get(old_name)
        if not telescope:
            return False
            
        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(telescope, key):
                setattr(telescope, key, value)
        
        # Handle name change
        if 'name' in kwargs and kwargs['name'] != old_name:
            new_name = kwargs['name']
            del self._telescopes[old_name]
            self._telescopes[new_name] = telescope
        
        self.save_equipment()
        self.equipment_updated.emit()
        logger.info(f"Updated telescope: {telescope.name}")
        return True
        
    def remove_telescope(self, name: str) -> bool:
        """Remove a telescope"""
        if name not in self._telescopes:
            return False
            
        del self._telescopes[name]
        self.save_equipment()
        self.equipment_updated.emit()
        logger.info(f"Removed telescope: {name}")
        return True
    
    # Camera methods
    def add_camera(self, camera: Camera):
        """Add a new camera"""
        self._cameras[camera.name] = camera
        self.save_equipment()
        self.equipment_updated.emit()
        logger.info(f"Added camera: {camera.name}")
        
    def get_camera(self, name: str) -> Optional[Camera]:
        """Get camera by name"""
        return self._cameras.get(name)
        
    def get_all_cameras(self) -> List[Camera]:
        """Get all cameras"""
        return list(self._cameras.values())
        
    def update_camera(self, old_name: str, **kwargs) -> bool:
        """Update camera properties"""
        camera = self._cameras.get(old_name)
        if not camera:
            return False
            
        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(camera, key):
                setattr(camera, key, value)
        
        # Handle name change
        if 'name' in kwargs and kwargs['name'] != old_name:
            new_name = kwargs['name']
            del self._cameras[old_name]
            self._cameras[new_name] = camera
        
        self.save_equipment()
        self.equipment_updated.emit()
        logger.info(f"Updated camera: {camera.name}")
        return True
        
    def remove_camera(self, name: str) -> bool:
        """Remove a camera"""
        if name not in self._cameras:
            return False
            
        del self._cameras[name]
        self.save_equipment()
        self.equipment_updated.emit()
        logger.info(f"Removed camera: {name}")
        return True


# Global equipment manager instance
equipment_manager = EquipmentManager()
