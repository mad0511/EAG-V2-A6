import logging
from typing import Dict, List, Optional
from models import DiagnosticState, UserPreferences
import json
from datetime import datetime

logger = logging.getLogger(__name__)

from formatting import print_layer_header, print_layer_output, print_separator
from rich.console import Console

console = Console()

class MemoryLayer:
    """
    Memory Layer - Manages persistence of diagnostic state and user preferences
    - Stores and retrieves diagnostic states
    - Maintains evidence history
    - Manages user preferences
    """
    
    def __init__(self, storage_path: str = "diagnostic_memory.json"):
        self.storage_path = storage_path
        self.current_state: Optional[DiagnosticState] = None
        logger.info("Initialized Memory Layer")
        
    def initialize_state(self, initial_hypotheses: Dict[str, float],
                        user_preferences: UserPreferences) -> DiagnosticState:
        """Initialize a new diagnostic state"""
        print_separator()
        print_layer_header("MEMORY LAYER")
        console.print("Retrieving stored preferences...")
        
        self.current_state = DiagnosticState(
            active_hypotheses=initial_hypotheses,
            evidence_history=[],
            confidence_threshold=0.8,  # Standard medical confidence threshold
            session_start_time=datetime.now().isoformat()
        )
        
        # Display memory contents
        print_layer_output({
            "Memory Output": {
                "Age": user_preferences.age,
                "Health Concerns": ", ".join(user_preferences.primary_health_concerns) or "None",
                "Medical History": ", ".join(user_preferences.medical_history) or "None",
                "Emergency Alerts": "Enabled" if user_preferences.emergency_contact else "Disabled",
                "Detailed Reports": "Enabled" if user_preferences.detailed_reports else "Disabled"
            }
        })
        
        self._save_state()
        return self.current_state
    
    def update_state(self, new_hypotheses: Dict[str, float], 
                    new_evidence: Dict) -> DiagnosticState:
        """Update the current diagnostic state with structured evidence"""
        if not self.current_state:
            raise ValueError("State not initialized")
            
        # Create structured evidence entry
        evidence_entry = {
            "timestamp": datetime.now().isoformat(),
            "symptoms": new_evidence.get("Detected Symptoms", []),
            "severity": new_evidence.get("Severity", 0),
            "duration": new_evidence.get("Duration", "unknown"),
            "description": new_evidence.get("Description", ""),
            "context": new_evidence.get("Context", "")
        }
        
        logger.debug(f"Updating state with structured evidence: {evidence_entry}")
        print_layer_header("MEMORY UPDATE")
        
        # Display memory update
        print_layer_output({
            "New Evidence": {
                "Symptoms": ", ".join(evidence_entry["symptoms"]) if evidence_entry["symptoms"] else "None",
                "Severity": f"{evidence_entry['severity']}/10",
                "Duration": evidence_entry["duration"],
                "Context": evidence_entry["context"] if evidence_entry["context"] else "None"
            }
        })
        
        # Update state
        self.current_state.active_hypotheses = new_hypotheses
        self.current_state.evidence_history.append(evidence_entry)
        
        self._save_state()
        return self.current_state
    
    def get_current_state(self) -> DiagnosticState:
        """Retrieve current diagnostic state"""
        if not self.current_state:
            raise ValueError("State not initialized")
        return self.current_state
    
    def _save_state(self) -> None:
        """Persist current state to storage"""
        if self.current_state:
            try:
                with open(self.storage_path, 'w') as f:
                    json.dump(self.current_state.model_dump(), f)
                logger.debug("State saved successfully")
            except Exception as e:
                logger.error(f"Error saving state: {e}")
    
    def _load_state(self) -> None:
        """Load state from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.current_state = DiagnosticState(**data)
            logger.debug("State loaded successfully")
        except FileNotFoundError:
            logger.warning("No saved state found")
        except Exception as e:
            logger.error(f"Error loading state: {e}")