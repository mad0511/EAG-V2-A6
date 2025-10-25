import logging
from rich.console import Console
from rich.prompt import Prompt, Confirm
from typing import Dict, List

class DiagnosticError(Exception):
    """Custom exception for diagnostic processing errors"""
    pass

from models import UserPreferences, DiagnosticInput, DiagnosticAction
from perception import PerceptionLayer
from memory import MemoryLayer
from decision import DecisionLayer
from action import ActionLayer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()

from formatting import print_layer_header, print_layer_output, print_separator, print_status, print_info
from datetime import datetime

class BayesianDiagnosticAgent:
    """Main agent class that orchestrates all cognitive layers"""
    
    def __init__(self):
        print_separator()
        console.print("[bold blue]Initializing Bayesian Diagnostic Agent...[/bold blue]")
        print_separator()
        
        self.user_preferences = self._get_user_preferences()
        
        print_separator()
        console.print("Establishing connection to MCP server...")
        print_status("Connection established, creating session...")
        print_status("Session created, initializing...")
        print_status("MCP server ready")
        
        # Initialize cognitive layers
        self.perception = PerceptionLayer(self.user_preferences)
        self.memory = MemoryLayer()
        self.decision = DecisionLayer(self.user_preferences)
        self.action = ActionLayer(self.user_preferences)
        
        timestamp = datetime.now().strftime("%m/%d/%y %H:%M:%S")
        print_separator()
        print_info(timestamp, "Processing request of type DiagnosticSession")
        
        logger.info("Bayesian Diagnostic Agent initialized")
    
    def _get_user_preferences(self) -> UserPreferences:
        """Gather user preferences through interactive prompts"""
        console.print("[bold blue]Welcome to the Medical Diagnostic Assistant![/bold blue]")
        console.print("To provide accurate diagnostic suggestions, please answer a few questions:\n")
        
        name = Prompt.ask("What is your name?")
        age = int(Prompt.ask("What is your age?"))
        
        console.print("\n[yellow]Do you have any of these ongoing health concerns?[/yellow]")
        console.print("1. Heart and Blood Pressure Issues")
        console.print("2. Diabetes or Blood Sugar")
        console.print("3. Respiratory Problems")
        console.print("4. Digestive Issues")
        console.print("5. Joint and Muscle Pain")
        console.print("6. None of the above")
        
        concerns_map = {
            "1": "Cardiovascular",
            "2": "Diabetes",
            "3": "Respiratory",
            "4": "Digestive",
            "5": "Musculoskeletal"
        }
        
        concerns_input = Prompt.ask(
            "Enter the numbers that apply (e.g., 1,3,4)",
            default="6"
        )
        health_concerns = []
        if concerns_input != "6":
            for num in concerns_input.split(','):
                if num.strip() in concerns_map:
                    health_concerns.append(concerns_map[num.strip()])
        
        console.print("\n[yellow]Do you have any previous medical conditions?[/yellow]")
        console.print("(e.g., Asthma, Hypertension, Diabetes)")
        medical_history = Prompt.ask("Enter conditions, or 'none'")
        medical_history = [] if medical_history.lower() == 'none' else [x.strip() for x in medical_history.split(',')]
        
        emergency_contact = Confirm.ask(
            "Should I suggest contacting emergency services for severe symptoms?",
            default=True
        )
        
        detailed_reports = Confirm.ask(
            "Would you like detailed medical explanations with your diagnosis?",
            default=True
        )
        
        return UserPreferences(
            name=name,
            age=age,
            primary_health_concerns=health_concerns,
            medical_history=medical_history,
            emergency_contact=emergency_contact,
            detailed_reports=detailed_reports
        )
    
    def start_diagnostic_session(self, initial_hypotheses: Dict[str, float]):
        """Start a new diagnostic session"""
        # Initialize memory with initial hypotheses
        self.memory.initialize_state(initial_hypotheses, self.user_preferences)
        logger.info("Started new diagnostic session")
        
        console.print("\n[bold green]Starting new diagnostic session[/bold green]")
        console.print("Enter your symptoms/evidence. Type 'exit' when done.\n")
        
        while True:
            try:
                # Get user input
                user_input = input("Please describe your symptoms (or type 'exit' to quit): ").strip()
                
                if user_input.lower() == 'exit':
                    break
                
                # Get severity rating
                try:
                    severity = int(Prompt.ask(
                        "Rate the severity (1-10)",
                        default="5"
                    ))
                    if severity < 1 or severity > 10:
                        raise ValueError("Severity must be between 1 and 10")
                except ValueError:
                    severity = 5
                    console.print("[yellow]Invalid severity rating, using default value of 5[/yellow]")
                
                # Get duration
                duration = Prompt.ask(
                    "How long have these symptoms been present?",
                    default="unknown"
                )
                
                # Create diagnostic input object
                diagnostic_input = DiagnosticInput(
                    description=user_input,
                    age=self.user_preferences.age,
                    symptoms=set(),  # Will be populated by perception layer
                    severity=severity,
                    duration=duration
                )
                
                try:
                    # 1. Input → Understanding [Perception]
                    # Process input through perception layer to understand symptoms and context
                    diagnostic_input = self.perception.process_input(user_input, diagnostic_input)
                    print_separator()
                    
                    # 2. Understanding → Refer to Past [Memory]
                    # Get current state and update memory with new understanding
                    current_state = self.memory.get_current_state()
                    
                    # Build evidence string with structured understanding
                    evidence = {
                        "Description": user_input,
                        "Detected Symptoms": list(diagnostic_input.symptoms),
                        "Severity": severity,
                        "Duration": duration,
                        "Context": diagnostic_input.additional_context
                    }
                    
                    # Update memory with structured evidence
                    self.memory.update_state(
                        current_state.active_hypotheses,
                        evidence
                    )
                    print_separator()
                    
                    # 3. Refer to Past → Decide [Decision]
                    # Make decision based on current understanding and memory
                    decision = self.decision.make_decision(current_state, diagnostic_input)
                    print_separator()
                    
                except Exception as e:
                    logger.error(f"Error in cognitive processing: {str(e)}")
                    raise DiagnosticError("Error during cognitive processing") from e
                
                # Action Layer: Execute decision
                action = DiagnosticAction(
                    action_type=decision.recommended_action,
                    parameters={
                        "description": user_input,
                        "detected_symptoms": ",".join(diagnostic_input.symptoms)
                    },
                    priority=1 if severity > 7 else 2,
                    requires_confirmation=severity > 8
                )
                
                # Execute the action
                self.action.execute_action(action, current_state.active_hypotheses)
                
                # Ask if user wants to continue
                console.print("\n[bold cyan]Would you like to:[/bold cyan]")
                console.print("1. Add more symptoms/evidence")
                console.print("2. Get final diagnosis and exit")
                choice = Prompt.ask("Choose an option", choices=["1", "2"], default="1")
                
                if choice == "2":
                    console.print("\n[bold blue]Finalizing diagnosis...[/bold blue]")
                    final_action = DiagnosticAction(
                        action_type="make_diagnosis",
                        parameters={"final": "true"},
                        priority=1,
                        requires_confirmation=False
                    )
                    self.action.execute_action(final_action, current_state.active_hypotheses)
                    break
                    
            except KeyboardInterrupt:
                logger.info("Session terminated by user")
                break
                
            except Exception as e:
                logger.error(f"Error processing input: {str(e)}")
                console.print(f"[red]An error occurred: {str(e)}[/red]")
                continue

            except KeyboardInterrupt:
                logger.info("Session terminated by user")
                break
                
            except Exception as e:
                logger.error(f"Error processing input: {str(e)}")
                console.print(f"[red]An error occurred: {str(e)}[/red]")


def get_initial_hypotheses(health_concerns: List[str], medical_history: List[str]) -> Dict[str, float]:
    """Generate initial hypotheses based on user's health concerns and history"""
    hypotheses = {}
    
    # Base conditions that are always possible
    base_conditions = {
        "Common Cold": 0.1,
        "Flu": 0.1,
        "Viral Infection": 0.1,
        "Fatigue": 0.1
    }
    hypotheses.update(base_conditions)
    
    # Add conditions based on health concerns
    concern_conditions = {
        "Cardiovascular": {
            "Hypertension": 0.2,
            "Arrhythmia": 0.15,
            "Angina": 0.15
        },
        "Diabetes": {
            "Type 2 Diabetes": 0.2,
            "Hypoglycemia": 0.15,
            "Diabetic Neuropathy": 0.15
        },
        "Respiratory": {
            "Asthma": 0.2,
            "Bronchitis": 0.15,
            "COPD": 0.15
        },
        "Digestive": {
            "Gastritis": 0.2,
            "IBS": 0.15,
            "Acid Reflux": 0.15
        },
        "Musculoskeletal": {
            "Arthritis": 0.2,
            "Back Pain": 0.15,
            "Muscle Strain": 0.15
        }
    }
    
    # Add relevant conditions based on user's concerns
    for concern in health_concerns:
        if concern in concern_conditions:
            hypotheses.update(concern_conditions[concern])
    
    # Adjust probabilities based on medical history
    for condition in medical_history:
        if condition in hypotheses:
            hypotheses[condition] *= 1.5  # Increase probability for known conditions
    
    # Normalize probabilities
    total = sum(hypotheses.values())
    return {k: v/total for k, v in hypotheses.items()}


if __name__ == "__main__":
    agent = BayesianDiagnosticAgent()
    initial_hypotheses = get_initial_hypotheses(
        agent.user_preferences.primary_health_concerns,
        agent.user_preferences.medical_history
    )
    agent.start_diagnostic_session(initial_hypotheses)