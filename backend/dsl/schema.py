from pydantic import BaseModel, Field
from typing import Literal

class TimingAssertion(BaseModel):
    assertion_type: Literal["timing"] = "timing"
    pin_number: int
    expected_period_ms: float
    tolerance_ms: float
    min_toggles: int

class LevelAssertion(BaseModel):
    assertion_type: Literal["level"] = "level"
    pin_number: int
    expected_level: Literal["HIGH", "LOW"]
    timestamp_ms: float

class ProtocolAssertion(BaseModel):
    assertion_type: Literal["protocol"] = "protocol"
    protocol_type: str
    address: str
    expected_response: str

class SerialAssertion(BaseModel):
    assertion_type: Literal["serial"] = "serial"
    expected_patterns: list[str] = Field(default_factory=list)
    max_nan_ratio: float = 0.5
    min_lines: int = 1