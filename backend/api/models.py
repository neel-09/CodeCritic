from pydantic import BaseModel, Field
from typing import Dict, Any, Literal, Optional

class GenerateRequest(BaseModel):
    prompt: str
    board: str = Field(default="Arduino Uno", description="Target hardware board")
    fqbn: str = Field(default="arduino:avr:uno", description="Fully Qualified Board Name for Arduino CLI")

# class GenerateResult(BaseModel):
#     sketch_ino: str
#     diag_json: str
#     pass_score: float
#     assertion_diff: Dict[str, Any]
#     session_id: str
