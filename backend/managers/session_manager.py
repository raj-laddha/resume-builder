from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timedelta
import asyncio
import os
from fastapi import WebSocket
from ..models.schemas import SessionData
from ..agents.agent_team import ResumeTeam
from ..helpers.websocket_handler import WebSocketHandler
from ..db.in_memory_db import db
from ..toolbox.session_tools import SessionTools
from ..helpers.logger import get_logger
logger = get_logger(__name__)

# Get configuration from environment variables with defaults
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 1800))  # 30 minutes default
SESSION_CLEANUP_INTERVAL = int(os.getenv('SESSION_CLEANUP_INTERVAL', 300))  # 5 minutes default

class SessionManager:
    def __init__(self, session_timeout: int = SESSION_TIMEOUT):
        self._sessions: Dict[str, SessionData] = {}
        self._session_timeout = session_timeout
        # Start cleanup task
        asyncio.create_task(self._periodic_cleanup())
    
    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = SessionData(
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            user_profile=None,
            job_description=None,
            resume_store={},
            resume_team=ResumeTeam(session_id=session_id, session_tools=SessionTools(session_id=session_id, session_manager=self)),
            websocket_handler=WebSocketHandler(session_id=session_id, session_manager=self)
        )
        
        db.create_session_record(session_id)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data by ID."""
        session = self._sessions.get(session_id)
        
        if session:
            db_session = db.get_session_record(session_id)
            session.job_description = db_session.job_description
            session.user_profile = db_session.user_profile
            session.resume_store = db_session.resume_store
        
        return session
    
    def update_websocket(self, session_id: str, websocket: WebSocket) -> bool:
        """Update websocket for a session."""
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        
        if not session.websocket_handler:
            return False
        
        session.websocket_handler.set_websocket(websocket)
        session.last_updated = datetime.utcnow()
        
        return True
    
    def get_websocket_handler(self, session_id: str) -> Optional[WebSocketHandler]:
        """Update websocket for a session."""
        
        if session_id not in self._sessions:
            return None
        
        return self._sessions[session_id].websocket_handler
    
    def update_user_profile(self, session_id: str, user_profile: Dict[str, Any]) -> bool:
        """Update resume data for a session."""
        if session_id not in self._sessions:
            return False
        
        updated = db.update_user_profile(session_id=session_id, user_profile=user_profile)
        if not updated:
            return False
        
        self._sessions[session_id].last_updated = datetime.utcnow()
        return True
    
    def update_job_description(self, session_id: str, job_description: str) -> bool:
        """Update job description for a session."""
        if session_id not in self._sessions:
            return False
        
        updated = db.update_job_description(session_id=session_id, job_description=job_description)
        if not updated:
            return False
        
        self._sessions[session_id].last_updated = datetime.utcnow()
        return True
    
    def update_resume_markdown(self, session_id: str, resume_markdown: str, version: Optional[int]=None) -> bool:
        """Update resume markdown for a session."""
        if session_id not in self._sessions:
            return False
        
        updated = db.update_resume_markdown(session_id=session_id, resume_markdown=resume_markdown, version=version)
        if not updated:
            return False

        self._sessions[session_id].last_updated = datetime.utcnow()
        return True
    
    def get_resume_markdown(self, session_id: str, version: Optional[int]=None) -> Optional[str]:
        """Update resume markdown for a session."""
        if session_id not in self._sessions:
            return None
        
        return db.get_resume_markdown(session_id=session_id, version=version)
    
    def get_resume_versions(self, session_id: str) -> list:
        """Get a list of all resume version numbers for a session."""
        
        session = self.get_session(session_id=session_id)
        
        if not session:
            return []
        
        return sorted(session.resume_store.keys())
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id not in self._sessions:
            return False
        
        db.delete_session_record(session_id=session_id)
        del self._sessions[session_id]
        return True
    
    def is_valid_session(self, session_id: str) -> bool:
        """Checks is a session is valid"""
        session = self.get_session(session_id)
        
        if not session:
            return False
        
        return not self._is_session_expired(session)
    
    def _is_session_expired(self, session: SessionData) -> bool:
        """Check if a session has expired."""
        now = datetime.utcnow()
        return (now - session.last_updated) > timedelta(seconds=self._session_timeout)
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return the number of sessions cleaned up."""
        expired_sessions = [
            session_id for session_id, session in self._sessions.items()
            if self._is_session_expired(session)
        ]
        
        for session_id in expired_sessions:
            self.delete_session(session_id=session_id)
        
        return len(expired_sessions)
    
    async def _periodic_cleanup(self):
        """Periodically clean up expired sessions."""
        while True:
            try:
                cleaned = self.cleanup_expired_sessions()
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} expired sessions")
            except Exception as e:
                logger.error(f"Error during session cleanup: {e}")
            
            # Run cleanup at configured interval
            await asyncio.sleep(SESSION_CLEANUP_INTERVAL)

# Create a global instance with configured timeout
session_manager = SessionManager() 