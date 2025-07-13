from typing import Dict, Any, Optional
from fastapi import WebSocket

class WebSocketHandler:
    """
    Handles WebSocket message processing for the resume builder application.
    """
    
    def __init__(self, session_id: str, session_manager: any, websocket: Optional[WebSocket] = None):
        self.session_id = session_id
        self.websocket = websocket
        self.session_manager = session_manager
    
    def set_websocket(self, websocket: WebSocket):
        self.websocket = websocket
    
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Process incoming WebSocket messages and route them to appropriate handlers.
        
        Args:
            websocket: The WebSocket connection
            message: The incoming message
        """
        if self.websocket is None:
            return
        
        message_type = message.get("type")
        message_handler = {
            "connect": self._handle_connect,
            "generate": self._handle_generate,
            "user_message": self._handle_user_message
        }
        
        if message_type in message_handler:
            await message_handler[message_type](message)
    
    
    async def _handle_connect(self, message: Dict[str, Any]) -> None:
        """
        Handle initial connection with session ID.
        
        Args:
            websocket: The WebSocket connection
            message: The message containing session ID
        """
        await self.websocket.send_json({
            "type": "connected",
            "session_id": self.session_id
        })
    
    async def _handle_generate(self, message: Dict[str, Any]) -> None:
        """
        Handle resume generation requests.
        
        Args:
            websocket: The WebSocket connection
            message: The message containing session ID
        """
        await self.websocket.send_json({
            "type": "agent_response_in_progress"
        })
        
        try:
            # Get session data
            session = self.session_manager.get_session(self.session_id)
            if not session:
                await self.websocket.send_json({
                    "type": "error",
                    "message": "Something went wrong. Please refresh."
                })
                return
        
            # Get resume data and job description from session
            user_profile = session.user_profile
            job_description = session.job_description
            
            if not user_profile or not job_description:
                await self.websocket.send_json({
                    "type": "error",
                    "message": "Missing user profile or job description. Please upload again."
                })
                return
            
            await session.resume_team.generate_resume()
            
        except Exception as e:
            await self.websocket.send_json({
                "type": "error",
                "message": "Something went wrong while generating resume. Please try again"
            })
        
        finally:
            await self.websocket.send_json({
                "type": "agent_response_completed"
            })
            
    
    async def _handle_user_message(self, message: Dict[str, Any]) -> None:
        """
        Handle feedback processing requests.
        
        Args:
            websocket: The WebSocket connection
            message: The message containing feedback
        """
        await self.websocket.send_json({
            "type": "agent_response_in_progress"
        })
        
        user_text = message.get("message", "").strip()
        if not user_text:
            await self.websocket.send_json({
                "type": "error",
                "message": "No message found. Please enter some message"
            })
            return
        
        try:
            # Get session data
            session = self.session_manager.get_session(self.session_id)
            if not session:
                await self.websocket.send_json({
                    "type": "error",
                    "message": "Something went wrong. Please refresh."
                })
                return
            
            # Process user message
            await session.resume_team.process_user_message(user_text)
            
        except Exception as e:
            await self.websocket.send_json({
                "type": "error",
                "message": "Something went wrong while processing your request. Please try again"
            })
        
        finally:
            await self.websocket.send_json({
                "type": "agent_response_completed"
            })
    
    async def trigger_resume_updated_event(self, resume_markdown: str) -> None:
        """
        Trigger the resume updated event to the client.
        Args:
            resume_markdown: Resume data to be updated

        Returns:
            None
        """
        
        if not self.websocket:
            return
        
        await self.websocket.send_json ({
            "type": "resume_updated",
            "data": resume_markdown
        })
    
    async def send_agent_response(self, message: str) -> None:
        """
        Sends message by the agent to be communicated with the client
        
        Args:
            message: Message to be sent to the user

        Returns:
            None
        """
        
        if not self.websocket:
            return
        
        await self.websocket.send_json({
            "type": "agent_response",
            "message": message
        })