from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..managers.session_manager import SessionManager

class SessionTools:
    def __init__(self, session_id: str, session_manager: 'SessionManager') -> None:
        self._session_id = session_id
        self._session_manager = session_manager
        
    def get_user_profile(self) -> str:
        """
        Get the user's resume profile from the session.
            
        Returns:
            str: The user's resume profile or an error message if not found
        """
        session = self._session_manager.get_session(session_id=self._session_id)
        if not session:
            return "Error: Session not found"
        
        profile_content = session.user_profile.content
        if not profile_content:
            return "Error: No resume data found in session"
        
        return str(profile_content)

    def get_job_description(self) -> str:
        """
        Get the job description from the session.
            
        Returns:
            str: The job description or an error message if not found
        """
        session = self._session_manager.get_session(session_id=self._session_id)

        if not session:
            return "Error: Session not found"
        
        job_description = session.job_description
        if not job_description:
            return "Error: No job description found in session"
        
        return str(job_description)

    def save_resume_markdown(self, resume_markdown: str, version: Optional[int]=None) -> str:
        """
        Save resume markdown to the session.
        
        Args:
            resume_markdown: The new resume markdown to save,
            version: Optional. The resume version to save
            
        Returns:
            str: Success message or error message if save failed
        """
        session = self._session_manager.get_session(session_id=self._session_id)
        if not session:
            return "Error: Session not found"
        
        if not resume_markdown:
            return "Error: Resume markdown cannot be empty"
        
        if self._session_manager.update_resume_markdown(session_id=self._session_id, resume_markdown=resume_markdown, version=version):
            return "Success: Resume markdown saved successfully"
        else:
            return "Error: Failed to save resume markdown"

    def get_resume_markdown(self, version: Optional[int] = None) -> str:
        """
        Get resume markdown from the session.
        
        Args:
            version: Optional. The resume version to fetch
            
        Returns:
            str: The resume markdown or an error message if not found
        """
        resume_markdown = self._session_manager.get_resume_markdown(session_id=self._session_id, version=version)
        
        if not resume_markdown:
            return "Error: No resume markdown found for the session"
        
        return str(resume_markdown)


    def get_resume_versions(self) -> str:
        """
        Get resume versions for the session.
            
        Returns:
            str: List of available versions
        """
        versions = self._session_manager.get_resume_versions(session_id=self._session_id)
        
        return str(versions)
    
    async def trigger_resume_updated_event(self, version: Optional[int] = None) -> None:
        """
        Trigger the resume updated event to the client.
        
        Args:
            version: Optional. The resume version to render. If not provided, the latest resume will be rendered

        Returns:
            None
        """
        
        resume_markdown = self._session_manager.get_resume_markdown(session_id=self._session_id, version=version)
        if not resume_markdown:
            return
        
        socket_handler = self._session_manager.get_websocket_handler(session_id=self._session_id)
        if not socket_handler:
            return
        
        await socket_handler.trigger_resume_updated_event(resume_markdown=resume_markdown)
        
    async def send_agent_response(self, message: str) -> None:
        """
        Sends message by the agent to be communicated with the client
        
        Args:
            message: Message to be sent to the user

        Returns:
            None
        """
        
        socket_handler = self._session_manager.get_websocket_handler(session_id=self._session_id)
        if not socket_handler:
            return

        await socket_handler.send_agent_response(message=message)