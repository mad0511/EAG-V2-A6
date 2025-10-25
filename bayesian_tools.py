import math
from dataclasses import dataclass, asdict
from typing import Dict, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import json
from rich.console import Console

console = Console(stderr=True)
mcp = FastMCP("BayesianDiagnostician")

class InvalidBeliefsError(Exception):
    """Raised when belief state is invalid."""
    pass

class BeliefsNotInitializedError(Exception):
    """Raised when trying to access uninitialized beliefs."""
    pass

@dataclass
class StateManager:
    """A class to manage and persist belief state between tool invocations."""
    _beliefs: Dict[str, float]
    _instance: Optional['StateManager'] = None

    @classmethod
    def get_instance(cls) -> 'StateManager':
        """Get the singleton instance of StateManager."""
        if cls._instance is None:
            cls._instance = StateManager({})
        return cls._instance

    @property
    def beliefs(self) -> Dict[str, float]:
        """Get current belief state."""
        if not self._beliefs:
            raise BeliefsNotInitializedError("Belief state has not been initialized.")
        return self._beliefs.copy()

    def validate_beliefs(self, beliefs: Dict[str, float]) -> None:
        """Validate the belief state."""
        if not beliefs:
            raise InvalidBeliefsError("Beliefs dictionary cannot be empty.")
        if not all(isinstance(p, (int, float)) for p in beliefs.values()):
            raise InvalidBeliefsError("All belief probabilities must be numeric.")
        if any(p < 0 for p in beliefs.values()):
            raise InvalidBeliefsError("All belief probabilities must be non-negative.")
        total_prob = sum(beliefs.values())
        if not (0.99 <= total_prob <= 1.01):  # Allow small floating-point errors
            raise InvalidBeliefsError(f"Belief probabilities must sum to approximately 1.0 (got {total_prob})")

    def update_beliefs(self, new_beliefs: Dict[str, float]) -> None:
        """Update belief state with new values."""
        self.validate_beliefs(new_beliefs)
        self._beliefs = new_beliefs.copy()
        console.log(f"State updated with {len(new_beliefs)} hypotheses. Sum of probabilities: {sum(new_beliefs.values()):.4f}")

    def clear_beliefs(self) -> None:
        """Clear current belief state."""
        self._beliefs = {}

def _normalize_beliefs(beliefs: Dict[str, float]) -> Dict[str, float]:
    """Normalize probabilities to sum to 1."""
    total_prob = sum(beliefs.values())
    if total_prob == 0:
        return beliefs
    return {h: p / total_prob for h, p in beliefs.items()}

@mcp.tool()
def initialize_beliefs(priors: dict) -> TextContent:
    """Initializes the belief state with prior probabilities for each hypothesis."""
    try:
        state = StateManager.get_instance()
        console.print(f"[blue]FUNCTION CALL:[/blue] initialize_beliefs()")
        
        if not priors:
            raise InvalidBeliefsError("Prior probabilities cannot be empty.")
        
        normalized_priors = _normalize_beliefs(priors)
        state.update_beliefs(normalized_priors)
        current_beliefs = state.beliefs
        
        table = Table(title="Initial Belief State (Priors)", box=None)
        table.add_column("Hypothesis (Disease)", style="cyan")
        table.add_column("Probability", style="magenta")
        for hypothesis, prob in current_beliefs.items():
            table.add_row(hypothesis, f"{prob:.4f}")
        console.print(table)
        console.file.flush()
        
        console.log("[green]Successfully initialized beliefs[/green]")
        return TextContent(type="text", text=f"Beliefs initialized: {json.dumps(current_beliefs)}")
    except (InvalidBeliefsError, BeliefsNotInitializedError) as e:
        error_msg = f"Error initializing beliefs: {str(e)}"
        console.print(f"[red]{error_msg}[/red]")
        return TextContent(type="text", text=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        console.print(f"[red]{error_msg}[/red]")
        return TextContent(type="text", text=error_msg)

@mcp.tool()
def update_belief_with_evidence(evidence: str, likelihoods: dict) -> TextContent:
    """Updates beliefs using Bayes' theorem given new evidence and its likelihoods."""
    try:
        state = StateManager.get_instance()
        console.print(f"[blue]FUNCTION CALL:[/blue] update_belief_with_evidence(evidence='{evidence}')")
        
        if not evidence:
            raise ValueError("Evidence string cannot be empty.")
        if not likelihoods:
            raise InvalidBeliefsError("Likelihood dictionary cannot be empty.")

        current_beliefs = state.beliefs  # This may raise BeliefsNotInitializedError
        
        # Validate that likelihoods contain all current hypotheses
        missing_hypotheses = set(current_beliefs.keys()) - set(likelihoods.keys())
        if missing_hypotheses:
            raise InvalidBeliefsError(f"Missing likelihoods for hypotheses: {missing_hypotheses}")

        # Bayes' Theorem: P(H|E) = P(E|H) * P(H) / P(E)
        
        # Calculate the numerator: P(E|H) * P(H)
        posteriors_unnormalized = {
            hypo: likelihoods.get(hypo, 0.0) * current_beliefs.get(hypo, 0.0)
            for hypo in current_beliefs
        }
        
        # Calculate the marginal probability of the evidence P(E) = sum(P(E|H) * P(H))
        marginal_evidence_prob = sum(posteriors_unnormalized.values())
        
        if marginal_evidence_prob == 0:
            raise InvalidBeliefsError(f"Evidence '{evidence}' is impossible given current beliefs. Cannot update.")

        # Calculate the new posterior probabilities P(H|E)
        new_posteriors = {
            hypo: p / marginal_evidence_prob
            for hypo, p in posteriors_unnormalized.items()
        }
        
        state.update_beliefs(new_posteriors)
        current_beliefs = state.beliefs
        
        table = Table(title=f"Updated Beliefs after Evidence: '{evidence}'", box=None)
        table.add_column("Hypothesis", style="cyan")
        table.add_column("Prior", style="magenta")
        table.add_column("Likelihood P(E|H)", style="yellow")
        table.add_column("New Posterior P(H|E)", style="green", justify="right")
        
        for hypo in current_beliefs:
            prior = current_beliefs[hypo] / (likelihoods.get(hypo, 0) / marginal_evidence_prob if likelihoods.get(hypo, 0) > 0 else 1)
            table.add_row(
                hypo,
                f"{prior:.4f}",
                f"{likelihoods.get(hypo, 0.0):.4f}",
                f"[bold]{current_beliefs[hypo]:.4f}[/bold]"
            )
        console.print(table)
        console.file.flush()

        console.log("[green]Successfully updated beliefs[/green]")
        return TextContent(type="text", text=json.dumps(current_beliefs))
    except (InvalidBeliefsError, BeliefsNotInitializedError, ValueError) as e:
        error_msg = f"Error updating beliefs: {str(e)}"
        console.print(f"[red]{error_msg}[/red]")
        return TextContent(type="text", text=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        console.print(f"[red]{error_msg}[/red]")
        return TextContent(type="text", text=error_msg)

@mcp.tool()
def get_current_diagnosis() -> TextContent:
    """Gets the current probability distribution over the hypotheses."""
    try:
        state = StateManager.get_instance()
        current_beliefs = state.beliefs  # This may raise BeliefsNotInitializedError
        console.print(f"[blue]FUNCTION CALL:[/blue] get_current_diagnosis()")
        
        table = Table(title="Current Diagnosis", box=None)
        table.add_column("Hypothesis", style="cyan")
        table.add_column("Probability", style="magenta", justify="right")
        
        sorted_beliefs = sorted(current_beliefs.items(), key=lambda item: item[1], reverse=True)
        
        for hypo, prob in sorted_beliefs:
            table.add_row(hypo, f"[bold]{prob:.4f}[/bold]")
        console.print(table)
        console.file.flush()
        
        console.log("[green]Successfully retrieved current diagnosis[/green]")
        return TextContent(type="text", text=json.dumps(current_beliefs))
    except BeliefsNotInitializedError as e:
        error_msg = f"Error retrieving diagnosis: {str(e)}"
        console.print(f"[red]{error_msg}[/red]")
        return TextContent(type="text", text=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        console.print(f"[red]{error_msg}[/red]")
        return TextContent(type="text", text=error_msg)

@mcp.tool()
def clear_diagnostic_state() -> TextContent:
    """Clears the current diagnostic state, resetting all beliefs."""
    try:
        state = StateManager.get_instance()
        state.clear_beliefs()
        console.log("[green]Successfully cleared diagnostic state[/green]")
        return TextContent(type="text", text="Diagnostic state cleared")
    except Exception as e:
        error_msg = f"Error clearing state: {str(e)}"
        console.print(f"[red]{error_msg}[/red]")
        return TextContent(type="text", text=error_msg)

def cleanup():
    """Perform cleanup operations before shutdown."""
    try:
        state = StateManager.get_instance()
        state.clear_beliefs()
        console.log("[green]Cleaned up state before shutdown[/green]")
    except Exception as e:
        console.print(f"[red]Error during cleanup: {str(e)}[/red]")

if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    finally:
        cleanup()
