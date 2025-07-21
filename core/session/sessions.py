from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from PySide6.QtCore import QObject, Signal
import json
import uuid
import logging

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Session states"""
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


@dataclass
class Session:
    """Represents an astrophotography session"""
    id: str
    target: str
    settings: Optional['SettingProfile'] = None
    telescope: Optional['Telescope'] = None
    camera: Optional['Camera'] = None
    exposures: int = 10
    state: SessionState = SessionState.PLANNED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    folder: Path = field(default_factory=lambda: Path("./sessions"))
    
    def __post_init__(self):
        """Initialize after dataclass creation"""
        # Create session folder if it doesn't exist
        self.folder.mkdir(parents=True, exist_ok=True)
        
    @property
    def telescope_name(self) -> str:
        """Get telescope name"""
        return self.telescope.name if self.telescope else ""
    
    @property
    def camera_name(self) -> str:
        """Get camera name"""
        return self.camera.name if self.camera else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization"""
        return {
            "id": self.id,
            "target": self.target,
            "settings": self.settings.as_dict() if self.settings else None,
            "telescope_name": self.telescope_name,
            "camera_name": self.camera_name,
            "exposures": self.exposures,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "folder": str(self.folder)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], equipment_manager, settings_profiles) -> 'Session':
        """Create session from dictionary"""
        # Get equipment objects
        telescope = equipment_manager.get_telescope(data.get("telescope_name")) if data.get("telescope_name") else None
        camera = equipment_manager.get_camera(data.get("camera_name")) if data.get("camera_name") else None
        
        # Get settings profile
        settings = None
        if data.get("settings"):
            settings_name = data["settings"].get("name", "default")
            settings = settings_profiles.get_profile(settings_name)
        
        return cls(
            id=data["id"],
            target=data["target"],
            settings=settings,
            telescope=telescope,
            camera=camera,
            exposures=data.get("exposures", 10),
            state=SessionState(data.get("state", "Planned")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            folder=Path(data.get("folder", "./data/sessions"))
        )


class SessionManager(QObject):
    """Manages astrophotography sessions"""
    
    current_session_changed = Signal(object)  # Signal when current session changes
    
    def __init__(self):
        super().__init__()
        self._sessions: Dict[str, Session] = {}
        self._current_session: Optional[Session] = None
        self._sessions_file = Path("./config/sessions.json")
        self._equipment_manager = None
        self._settings_profiles = None
        
    def set_dependencies(self, equipment_manager, settings_profiles):
        """Set dependencies after initialization"""
        self._equipment_manager = equipment_manager
        self._settings_profiles = settings_profiles
        
    def load_sessions(self):
        """Load sessions from file"""
        try:
            if self._sessions_file.exists():
                with open(self._sessions_file, 'r') as f:
                    data = json.load(f)
                    
                for session_data in data.get("sessions", []):
                    try:
                        session = Session.from_dict(session_data, self._equipment_manager, self._settings_profiles)
                        self._sessions[session.id] = session
                    except Exception as e:
                        logger.error(f"Failed to load session {session_data.get('id', 'unknown')}: {e}")
                        
                logger.info(f"Loaded {len(self._sessions)} sessions")
            else:
                logger.info("No sessions file found, starting with empty session list")
                
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            
    def save_sessions(self):
        """Save sessions to file"""
        try:
            self._sessions_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "sessions": [session.to_dict() for session in self._sessions.values()]
            }
            
            with open(self._sessions_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(self._sessions)} sessions")
            
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
            
    def create_session(self, target: str, settings: Optional['SettingProfile'] = None, 
                      telescope: Optional['Telescope'] = None, camera: Optional['Camera'] = None, 
                      exposures: int = 10) -> Session:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        
        session = Session(
            id=session_id,
            target=target,
            settings=settings,
            telescope=telescope,
            camera=camera,
            exposures=exposures
        )
        
        self._sessions[session_id] = session
        self.save_sessions()
        
        logger.info(f"Created session: {target} (ID: {session_id})")
        return session
        
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return self._sessions.get(session_id)
        
    def get_all_sessions(self) -> List[Session]:
        """Get all sessions"""
        return list(self._sessions.values())
        
    def update_session(self, session_id: str, **kwargs) -> bool:
        """Update session properties"""
        session = self._sessions.get(session_id)
        if not session:
            return False
            
        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
                
        # Update timestamp
        session.updated_at = datetime.now(timezone.utc)
        
        self.save_sessions()
        logger.info(f"Updated session: {session.target}")
        return True
        
    def remove_session(self, session_id: str) -> bool:
        """Remove a session"""
        session = self._sessions.get(session_id)
        if not session:
            return False
            
        del self._sessions[session_id]
        self.save_sessions()
        
        # Clear current session if it was deleted
        if self._current_session and self._current_session.id == session_id:
            self.set_current_session(None)
            
        logger.info(f"Removed session: {session.target}")
        return True
        
    def set_current_session(self, session_id: Optional[str]):
        """Set the current session"""
        if session_id is None:
            self._current_session = None
        else:
            self._current_session = self._sessions.get(session_id)
            
        self.current_session_changed.emit(self._current_session)
        
    def get_current_session(self) -> Optional[Session]:
        """Get the current session"""
        return self._current_session


# Global session manager instance
session_manager = SessionManager()
