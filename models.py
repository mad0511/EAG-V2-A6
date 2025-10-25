from pydantic import BaseModel
from typing import Dict, List, Optional, Set

# User Preference Models
class UserPreferences(BaseModel):
    """User preferences for diagnostic process"""
    name: str
    age: int
    primary_health_concerns: List[str]  # e.g., ["Heart Disease", "Diabetes"]
    medical_history: List[str]  # e.g., ["Hypertension", "Asthma"]
    emergency_contact: bool  # Whether to suggest emergency contact based on symptoms
    detailed_reports: bool  # Whether to show detailed medical explanations
    detail_level: str = "detailed"  # "detailed" or "basic"

# Perception Layer Models
class DiagnosticInput(BaseModel):
    """Raw input from user about symptoms/evidence"""
    description: str
    age: int
    symptoms: Set[str] = set()  # Detected symptoms
    severity: Optional[int] = None  # 1-10 scale
    duration: Optional[str] = None
    additional_context: Optional[str] = None

# Memory Layer Models
class DiagnosticState(BaseModel):
    """Current state of the diagnostic process"""
    active_hypotheses: Dict[str, float]  # disease -> probability
    evidence_history: List[str]
    confidence_threshold: float
    session_start_time: str

# Decision Layer Models
class DiagnosticDecision(BaseModel):
    """Decision about next diagnostic step"""
    recommended_action: str
    confidence_level: float
    alternative_actions: List[str]
    explanation: str

# Action Layer Models
class DiagnosticAction(BaseModel):
    """Output action to be taken"""
    action_type: str  # "update_beliefs", "request_info", "make_diagnosis"
    parameters: Dict[str, str]  # Changed from Dict[str, any] to Dict[str, str]
    priority: int
    requires_confirmation: bool