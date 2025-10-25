import logging
from typing import List, Dict
from models import DiagnosticState, DiagnosticDecision, UserPreferences, DiagnosticInput
from medical_knowledge import get_related_conditions, adjust_probabilities_for_age, check_emergency_symptoms

logger = logging.getLogger(__name__)

from formatting import print_layer_header, print_layer_output, print_separator, print_status
from rich.console import Console

console = Console()

class DecisionLayer:
    """
    Decision Layer - Makes diagnostic decisions based on current state
    - Analyzes current probabilities
    - Determines next actions
    - Incorporates user preferences in decision making
    """
    
    def __init__(self, user_preferences: UserPreferences):
        self.preferences = user_preferences
        self.confidence_threshold = 0.8  # Set a standard confidence threshold
        self.emergency_threshold = 0.9  # Threshold for emergency recommendations
        logger.info(f"Initialized Decision Layer with confidence threshold: {self.confidence_threshold}")
    
    def make_decision(self, current_state: DiagnosticState, input_data: DiagnosticInput) -> DiagnosticDecision:
        """Determine next action based on current diagnostic state and new input"""
        print_separator()
        print_layer_header("DECISION LAYER")
        console.print("[cyan]Analyzing current evidence and medical history...[/cyan]")
        
        # Review evidence history
        if current_state.evidence_history:
            latest_evidence = current_state.evidence_history[-1]
            console.print("Latest Evidence Analysis:")
            if isinstance(latest_evidence, dict):  # New structured format
                symptoms = latest_evidence.get("symptoms", [])
                severity = latest_evidence.get("severity", 0)
                duration = latest_evidence.get("duration", "unknown")
                context = latest_evidence.get("context", "")
                
                if symptoms:
                    console.print(f"[yellow]Detected Symptoms:[/yellow] {', '.join(symptoms)}")
                if severity >= 7:
                    console.print(f"[red]⚠️ High Severity:[/red] {severity}/10")
                if context:
                    console.print(f"[blue]Context:[/blue] {context}")
        
        console.print("\n[cyan]Making diagnostic decision...[/cyan]")
        
        # Add detailed explanation based on user preference
        if self.preferences.detailed_reports:
            console.print("[yellow]Analyzing symptom patterns and severity...[/yellow]")
            if input_data.severity >= 8:
                console.print("[red]⚠️ High severity detected - conducting thorough analysis[/red]")
        
        # Get conditions related to the symptoms
        related_conditions = get_related_conditions(input_data.symptoms)
        
        # Apply symptom-specific weights from condition details
        from medical_knowledge import CONDITION_DETAILS
        
        for condition, probability in related_conditions.items():
            if condition in CONDITION_DETAILS:
                condition_info = CONDITION_DETAILS[condition]
                if "symptom_weights" in condition_info:
                    weight_multiplier = 1.0
                    
                    # Apply specific symptom weights
                    for symptom in input_data.symptoms:
                        if symptom in condition_info["symptom_weights"]:
                            weight_multiplier *= condition_info["symptom_weights"][symptom]
                    
                    # Adjust for severity
                    if input_data.severity >= 7:
                        if "fever" in input_data.symptoms and condition in ["Flu", "Viral Infection", "COVID-19"]:
                            weight_multiplier *= 1.5
                        elif condition in ["Common Cold"]:
                            weight_multiplier *= 0.5  # Severe symptoms less likely for cold
                    
                    related_conditions[condition] *= weight_multiplier
            
        # Normalize probabilities
        total = sum(related_conditions.values())
        if total > 0:
            for condition in related_conditions:
                related_conditions[condition] /= total
        
        # Adjust probabilities based on age
        age_adjusted = adjust_probabilities_for_age(related_conditions, self.preferences.age)
        
        # Update current hypotheses with new information
        for condition, prob in age_adjusted.items():
            if condition in current_state.active_hypotheses:
                current_state.active_hypotheses[condition] = max(prob, current_state.active_hypotheses[condition])
            else:
                current_state.active_hypotheses[condition] = prob
        
        # Check for emergency symptoms
        emergency_warnings = check_emergency_symptoms(
            input_data.symptoms,
            list(current_state.active_hypotheses.keys())
        )
        
        # Get the most likely diagnosis
        sorted_hypotheses = sorted(
            current_state.active_hypotheses.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        top_hypothesis, top_probability = sorted_hypotheses[0]
        
        # Log emergency warnings if any
        if emergency_warnings and self.preferences.emergency_contact:
            for warning in emergency_warnings:
                logger.warning(warning)
        
        # Determine confidence level and recommended action
        if top_probability >= self.confidence_threshold:
            action = "make_diagnosis"
            confidence = top_probability
            alternatives = ["request_confirmation", "continue_observation"]
        elif len(current_state.evidence_history) < 3:
            action = "request_info"
            confidence = 0.5  # Medium confidence in needing more information
            alternatives = ["make_tentative_diagnosis", "refer_to_specialist"]
        else:
            action = "update_beliefs"
            confidence = 0.7  # High confidence in needing belief update
            alternatives = ["request_info", "make_tentative_diagnosis"]
        
        # Adjust based on user's detail level preference
        explanation = self._generate_explanation(
            action, top_hypothesis, top_probability,
            self.preferences.detail_level
        )
        
        decision = DiagnosticDecision(
            recommended_action=action,
            confidence_level=confidence,
            alternative_actions=alternatives,
            explanation=explanation
        )
        
        logger.info(f"Made decision: {action} with confidence {confidence:.2f}")
        return decision
    
    def _generate_explanation(self, action: str, hypothesis: str, 
                            probability: float, detail_level: str) -> str:
        """Generate an explanation for the decision at appropriate detail level"""
        if detail_level == "basic":
            return f"Recommended action: {action} based on current evidence."
        elif detail_level == "detailed":
            return (f"Recommended {action} because {hypothesis} has "
                   f"probability {probability:.2f}, which is "
                   f"{'above' if probability >= self.confidence_threshold else 'below'} "
                   f"the confidence threshold of {self.confidence_threshold}.")
        else:  # expert
            return (f"Technical analysis suggests {action} due to:\n"
                   f"- Top hypothesis: {hypothesis} (p={probability:.3f})\n"
                   f"- Confidence threshold: {self.confidence_threshold}\n"
                   f"- Statistical significance: {probability >= self.confidence_threshold}")
                   
    def evaluate_risk(self, hypothesis: str, probability: float) -> bool:
        """Evaluate if a hypothesis needs immediate attention based on risk tolerance"""
        high_risk_conditions = ["heart_attack", "stroke", "severe_infection"]
        if hypothesis in high_risk_conditions:
            # Lower threshold for high-risk conditions
            adjusted_threshold = self.confidence_threshold * 0.8
            return probability >= adjusted_threshold
        return probability >= self.confidence_threshold