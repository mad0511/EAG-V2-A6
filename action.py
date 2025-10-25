import logging
from typing import Dict, Optional
from models import DiagnosticAction, DiagnosticDecision, UserPreferences
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

class ActionLayer:
    """
    Action Layer - Executes diagnostic decisions and provides recommendations
    - Implements recommended actions
    - Handles user interactions
    - Manages diagnostic state updates
    - Provides detailed recommendations and precautions
    """
    
    def __init__(self, user_preferences: UserPreferences):
        self.preferences = user_preferences
        logger.info(f"Initialized Action Layer for user: {user_preferences.name}")
        
    def execute_action(self, action: DiagnosticAction, 
                      current_beliefs: Dict[str, float]) -> None:
        """Execute the specified diagnostic action"""
        logger.debug(f"Executing action: {action.action_type}")
        
        if action.action_type == "make_diagnosis":
            self._present_diagnosis(current_beliefs)
        elif action.action_type == "request_info":
            self._request_additional_info(action.parameters)
        elif action.action_type == "update_beliefs":
            self._show_belief_update(current_beliefs)
            
        if action.requires_confirmation:
            self._request_confirmation()
    
    def _present_diagnosis(self, beliefs: Dict[str, float]) -> None:
        """Present diagnostic results to the user"""
        sorted_beliefs = sorted(beliefs.items(), key=lambda x: x[1], reverse=True)
        
        is_final = len(sorted_beliefs) > 0 and sorted_beliefs[0][1] >= 0.8
        title = "[bold green]Final Diagnosis[/bold green]" if is_final else "Current Diagnostic Assessment"
        
        table = Table(title=title)
        table.add_column("Condition", style="cyan")
        table.add_column("Probability", style="magenta")
        table.add_column("Confidence", style="green")
        
        for condition, prob in sorted_beliefs:
            confidence = "High" if prob > 0.8 else "Medium" if prob > 0.5 else "Low"
            table.add_row(condition, f"{prob:.2%}", confidence)
        
        console.print(table)
        
        # Add recommendations based on top condition
        if sorted_beliefs:
            top_condition, top_prob = sorted_beliefs[0]
            if top_prob > 0.8:
                console.print(f"\n[bold green]Primary Diagnosis:[/bold green] {top_condition} ({top_prob:.1%} confidence)")
            else:
                console.print(f"\n[yellow]Tentative Assessment:[/yellow] {top_condition} ({top_prob:.1%} confidence)")
                console.print("[yellow]Note:[/yellow] More evidence may be needed for a definitive diagnosis.")
        
                # Add detailed medical explanations if requested
        if self.preferences.detailed_reports:
            if top_prob > 0.5:
                console.print("\n[bold cyan]Detailed Medical Information:[/bold cyan]")
                for condition, prob in sorted_beliefs[:3]:  # Show top 3 conditions
                    self._show_condition_details(condition, prob)
            else:
                console.print("\n[yellow]Note:[/yellow] More symptoms needed for detailed analysis")
            logger.debug(f"Full belief distribution: {beliefs}")
            
        # Add a visual separator
        console.print("\n" + "─" * 50 + "\n")
    
    def _request_additional_info(self, parameters: Dict) -> None:
        """Request additional information from the user"""
        question = parameters.get("question", "Please provide more information:")
        console.print(f"[yellow]{question}[/yellow]")
        logger.info("Additional information requested from user")
    
    def _show_belief_update(self, new_beliefs: Dict[str, float]) -> None:
        """Show how beliefs have been updated"""
        if not self.preferences.detailed_reports:
            console.print("[blue]Diagnostic beliefs updated[/blue]")
        else:
            table = Table(title="Updated Beliefs")
            table.add_column("Condition", style="cyan")
            table.add_column("New Probability", style="magenta")
            
            for condition, prob in new_beliefs.items():
                table.add_row(condition, f"{prob:.2%}")
            console.print(table)
    
    def _request_confirmation(self) -> None:
        """Request user confirmation for critical actions"""
        console.print("[red]Please confirm this action (y/n):[/red]")
        logger.info("Confirmation requested from user")
    
    def _show_condition_details(self, condition: str, probability: float) -> None:
        """Show detailed medical information for a condition"""
        condition_details = {
            "Type 2 Diabetes": {
                "Description": "A chronic condition affecting how your body processes blood sugar.",
                "Common Symptoms": "Increased thirst, frequent urination, fatigue, blurred vision",
                "Risk Factors": "Obesity, family history, age over 45, physical inactivity"
            },
            "Hypoglycemia": {
                "Description": "Low blood sugar condition, often related to diabetes treatment.",
                "Common Symptoms": "Shakiness, sweating, confusion, irregular heartbeat",
                "Risk Factors": "Diabetes medications, delayed meals, excessive exercise"
            },
            "Diabetic Neuropathy": {
                "Description": "Nerve damage caused by high blood sugar levels.",
                "Common Symptoms": "Numbness in feet/legs, burning sensation, muscle weakness",
                "Risk Factors": "Long-term diabetes, poor blood sugar control, smoking"
            },
            "Hypertension": {
                "Description": "High blood pressure condition affecting arterial walls.",
                "Common Symptoms": "Headaches, shortness of breath, nosebleeds",
                "Risk Factors": "Age, obesity, high sodium diet, stress"
            }
        }
        
        if condition in condition_details:
            details = condition_details[condition]
            console.print(f"\n[cyan]{condition}[/cyan] ({probability:.1%} probability)")
            for key, value in details.items():
                console.print(f"  [dim]{key}:[/dim] {value}")
        else:
            console.print(f"\n[cyan]{condition}[/cyan] ({probability:.1%} probability)")
            console.print("  Detailed information not available for this condition.")

    def notify_user(self, message: str, level: str = "info") -> None:
        """Send a notification to the user based on their preferences"""
        if self.preferences.emergency_contact and level == "critical":
            console.print(f"[bold red]MEDICAL ALERT:[/bold red] {message}")
        else:
            console.print(f"[{level}]{message}[/{level}]")
        logger.log(
            getattr(logging, level.upper()),
            f"User notification: {message}"
        )