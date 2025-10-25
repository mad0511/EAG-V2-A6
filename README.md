# Bayesian Diagnostic Agent

A cognitive architecture-based diagnostic system that uses Bayesian inference for medical diagnosis while adapting to user preferences and maintaining persistent state.

## Architecture

This system implements a four-layer cognitive architecture:

1. **Perception Layer** (`perception.py`)
   - Processes raw user input into structured diagnostic information
   - Adapts input processing based on user preferences
   - Validates and normalizes input data

2. **Memory Layer** (`memory.py`)
   - Maintains persistent diagnostic state
   - Tracks evidence history
   - Manages belief updates
   - Provides state retrieval and persistence

3. **Decision Layer** (`decision.py`)
   - Analyzes current diagnostic state
   - Makes decisions about next actions
   - Incorporates user risk tolerance
   - Generates explanations at appropriate detail levels

4. **Action Layer** (`action.py`)
   - Executes diagnostic actions
   - Presents results to users
   - Handles notifications and confirmations
   - Formats output based on user preferences

## Features

- Personalized diagnostics based on user preferences
- Multi-level explanations (basic, detailed, expert)
- Persistent state management
- Risk-aware decision making
- Rich console output with formatted tables
- Comprehensive logging system
- Type-safe data handling with Pydantic
- Interactive user preference collection

## Requirements

- Python 3.11+
- uv (Modern Python packaging tools)
- Dependencies:
  - pydantic
  - rich
  - mcp[cli]

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bayesian-diagnostic-agent.git
   cd bayesian-diagnostic-agent
   ```

2. Install uv if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Install project dependencies using uv:
   ```bash
   uv pip install pydantic rich "mcp[cli]"
   uv pip install -r requirements.txt
   ```

## Usage

1. Run the main application with uv:
   ```bash
   uv run main.py
   ```

2. Follow the interactive prompts to:
   - Set up your preferences
   - Input diagnostic information
   - Receive personalized diagnostic results

## Configuration

User preferences include:
- Preferred medical categories
- Risk tolerance level (0.0-1.0)
- Detail level for explanations
- Notification preferences

## File Structure

```
bayesian-diagnostic-agent/
├── main.py              # Main application entry point
├── models.py            # Pydantic data models
├── perception.py        # Perception layer implementation
├── memory.py           # Memory layer implementation
├── decision.py         # Decision layer implementation
├── action.py          # Action layer implementation
├── requirements.txt    # Project dependencies
└── README.md          # This file
```

## Design Principles

1. **Modularity**: Each cognitive layer is independent and focused
2. **Type Safety**: All data structures are validated with Pydantic
3. **Persistence**: State is maintained between sessions
4. **Personalization**: System adapts to user preferences
5. **Robustness**: Comprehensive error handling and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

