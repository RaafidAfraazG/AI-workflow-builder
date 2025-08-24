from pydantic import BaseModel
from typing import Any, Dict

class SuccessResponse(BaseModel):
    success: bool = True
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str