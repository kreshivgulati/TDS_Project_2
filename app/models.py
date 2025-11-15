from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any


class QuizRequest(BaseModel):
    """
    Input model for /quiz endpoint
    """
    secret: str
    url: HttpUrl


class QuizResponse(BaseModel):
    """
    Output model for /quiz endpoint
    """
    success: bool
    message: str
    answer: Optional[Any] = None
    submit_response: Optional[Any] = None


class PageContent(BaseModel):
    """
    Internal model: returned by browser renderer
    """
    url: str
    html: str
    text: str
    metadata: Optional[Dict[str, Any]] = None   # e.g. detected file links, script payloads, etc.
