from typing import Dict, Any, Optional
from datetime import datetime
import os
from ..models.schemas import UserProfileFile, DBSession

# Get configuration from environment variables with defaults
MAX_RESUMES_PER_SESSION = int(os.getenv('MAX_RESUMES_PER_SESSION', 5))

class InMemoryDB:
    def __init__(self):
        self._sessions: Dict[str, DBSession] = {}
    
    def create_session_record(self, session_id: str) -> DBSession:
        """Create a new session record."""
        
        if not session_id:
            raise ValueError('Session id cannot be empty')
        
        self._sessions[session_id] = DBSession(
            session_id=session_id,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            user_profile=None,
            job_description=None,
            resume_store={}
        )
        return self._sessions[session_id]
    
    def get_session_record(self, session_id: str) -> Optional[DBSession]:
        """Get session data by ID."""
        session = self._sessions.get(session_id)
        return session
    
    def update_user_profile(self, session_id: str, user_profile: Dict[str, Any]) -> bool:
        """Update resume data for a session."""
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        session.user_profile = UserProfileFile(
            filename=user_profile["filename"],
            content_type=user_profile["content_type"],
            size=user_profile["size"],
            content=user_profile["content"],
            parsed_at=datetime.fromisoformat(user_profile["parsed_at"])
        )
        session.last_updated = datetime.utcnow()
        return True
    
    def update_resume_markdown(self, session_id: str, resume_markdown: str, version: Optional[int]=None) -> bool:
        """Update resume markdown for a session."""
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        
        if version is None:
            version = max(session.resume_store.keys(), default=0) + 1
            
        session.resume_store[version] = resume_markdown
        
        # Enforce a maximum number of resumes
        if len(session.resume_store) > MAX_RESUMES_PER_SESSION:
            oldest_version = min(session.resume_store.keys())
            del session.resume_store[oldest_version]
            
        session.last_updated = datetime.utcnow()
        return True
    
    def get_resume_markdown(self, session_id: str, version: Optional[int]=None) -> Optional[str]:
        """Update resume markdown for a session."""
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
    
        if version is None:
            version = max(session.resume_store.keys(), default=0)
            
        if version not in session.resume_store:
            return None
            
        resume_markdown = session.resume_store[version]
        return resume_markdown
    
    def update_job_description(self, session_id: str, job_description: str) -> bool:
        """Update job description for a session."""
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        session.job_description = job_description
        session.last_updated = datetime.utcnow()
        return True
    
    def delete_session_record(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id not in self._sessions:
            return False
        
        del self._sessions[session_id]
        return True

# Create a global instance with configured timeout
db = InMemoryDB() 