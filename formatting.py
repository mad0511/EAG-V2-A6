from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()

def print_separator():
    """Print a separator line"""
    console.print("=" * 75)

def print_layer_header(name: str):
    """Print a layer header with icon and formatting"""
    icons = {
        "PERCEPTION": "🔍",
        "MEMORY": "💾",
        "DECISION": "🤔",
        "ACTION": "🎯"
    }
    icon = icons.get(name.upper(), "➡️")
    console.print(f"\n{icon} {name}: ", style="bold cyan", end="")

def print_layer_output(content: dict, indent: int = 2):
    """Print layer output in a structured format"""
    for key, value in content.items():
        console.print(" " * indent + f"{key}: ", style="dim", end="")
        if isinstance(value, dict):
            console.print()
            print_layer_output(value, indent + 2)
        else:
            console.print(f"{value}", style="bright_white")

def print_status(message: str, success: bool = True):
    """Print a status message with appropriate icon"""
    icon = "✅" if success else "❌"
    console.print(f"{icon} {message}")

def print_info(timestamp: str, message: str):
    """Print an info message with timestamp"""
    console.print(f"[{timestamp}] INFO    {message}", style="blue")