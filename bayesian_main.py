import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
import asyncio
from rich.console import Console
from rich.panel import Panel
import json

console = Console()

# Load environment variables and setup Gemini
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    console.print("[red]Error: GEMINI_API_KEY not found in environment variables.[/red]")
    exit()

client = genai.Client(api_key=api_key)

async def generate_with_timeout(client, prompt, timeout=30):
    """Generate content with a timeout"""
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        return response
    except Exception as e:
        console.print(f"[red]Error during generation: {e}[/red]")
        return None

async def main():
    try:
        console.print(Panel("Probabilistic Diagnostic Agent", border_style="purple"))

        server_params = StdioServerParameters(
            command="python",
            args=["bayesian_tools.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                system_prompt = """You are a meticulous Probabilistic Diagnostic Agent. Your goal is to identify the most likely disease using Bayesian inference, thinking step-by-step.

**1. Tools Available (Stateful):**
Your tools are stateful. The server will remember the probabilities between your calls.
- `initialize_beliefs(priors: dict)`: Sets the initial probability for each disease.
- `update_belief_with_evidence(evidence: str, likelihoods: dict)`: Updates probabilities based on a symptom.
- `get_current_diagnosis()`: Returns the current probability distribution.

**2. Core Principles (Your Internal Rules):**
- **Self-Check Priors:** Before initializing, you MUST verify that the prior probabilities sum to 1.0. If not, request a correction.
- **Check for Complete Data:** Before updating beliefs, you MUST verify that likelihoods are provided for ALL hypotheses. If not, request the missing data.

**3. Workflow & Output Format:**
Follow a strict "Reason -> Act" cycle. For each step, respond with your reasoning followed by one of the actions below.

- **Action Formats (Choose one per turn):**
    - `FUNCTION_CALL: function_name|json_payload`
    - `FINAL_ANSWER: [your final summary]`
    - `REQUEST_CORRECTION: [specific instruction to user about what data is missing/inconsistent]`

**Example Workflow:**
User: Analyze a patient with these priors: Flu: 0.5, Cold: 0.5.
Assistant:
REASONING: The priors sum to 1.0. I will initialize the beliefs.
FUNCTION_CALL: initialize_beliefs|{"priors": {"Flu": 0.5, "Cold": 0.5}}

User: Beliefs initialized. The patient has a fever. Likelihoods are Flu: 0.8, Cold: 0.6.
Assistant:
REASONING: The likelihoods are complete. I will update the beliefs.
FUNCTION_CALL: update_belief_with_evidence|{"evidence": "Fever", "likelihoods": {"Flu": 0.8, "Cold": 0.6}}

User: Beliefs updated.
Assistant:
REASONING: All evidence is processed. I will get the final diagnosis.
FUNCTION_CALL: get_current_diagnosis|{}

User: The final diagnosis is {"Flu": 0.5714, "Cold": 0.4286}.
Assistant:
REASONING: The final probabilities are calculated. Flu is the most likely diagnosis.
FINAL_ANSWER: [The most likely diagnosis is Flu, with a probability of 57.14%.]
"""

                problem = """A patient presents at a clinic. 
                The three most likely diseases are 'Viral Infection', 'Bacterial Infection', or 'Allergies'. 
                The base rates (priors) for these in the population are 60%, 30%, and 10% respectively. 
                The patient reports having a 'High Fever'. 
                The probability of a high fever given a viral infection is 70%, given a bacterial infection is 85%, and given allergies is 5%. Next, the patient reports 'Sneezing'. 
                The probability of sneezing given a viral infection is 50%, given a bacterial infection is 20%, and for allergies is 90%. 
                Determine the most likely diagnosis."""
                console.print(Panel(f"Problem: {problem}", border_style="purple"))

                prompt = f"{system_prompt}\n\nUser: {problem}"
                
                for _ in range(10): # Increased turn limit for more complex reasoning
                    response = await generate_with_timeout(client, prompt)
                    if not response or not response.text:
                        console.print("[red]No response from LLM.[/red]")
                        break

                    # Handle multi-line responses (Reasoning + Action)
                    raw_response = response.text.strip()
                    console.print(f"\n[yellow]Assistant:[/yellow]\n{raw_response}")
                    
                    # The action is the last line of the response
                    action_line = raw_response.splitlines()[-1].strip().strip('`')

                    if action_line.startswith("FUNCTION_CALL:"):
                        _, function_info = action_line.split(":", 1)
                        parts = function_info.split("|")
                        func_name = parts[0].strip().replace("()", "")
                        
                        try:
                            # Handle calls with no arguments
                            if func_name == "get_current_diagnosis":
                                tool_result = await session.call_tool(func_name)
                                prompt += f"\nAssistant: {raw_response}\nUser: The final diagnosis is {tool_result.content[0].text}. Please provide your final answer."
                                continue

                            # Handle calls with arguments
                            if len(parts) < 2:
                                raise ValueError("Function call is missing arguments.")

                            payload_str = parts[1].strip()
                            payload = json.loads(payload_str)

                            if func_name == "initialize_beliefs":
                                tool_result = await session.call_tool(func_name, arguments={"priors": payload})
                                prompt += f"\nAssistant: {raw_response}\nUser: Beliefs initialized. Now consider the first symptom."
                            
                            elif func_name == "update_belief_with_evidence":
                                evidence = payload.get("evidence")
                                likelihoods = payload.get("likelihoods")
                                tool_result = await session.call_tool(func_name, arguments={"evidence": evidence, "likelihoods": likelihoods})
                                prompt += f"\nAssistant: {raw_response}\nUser: Beliefs updated. Now consider the next symptom or finalize the diagnosis."

                        except Exception as e:
                            console.print(f"[red]Error processing tool call: {e}[/red]")
                            prompt += f"\nAssistant: {raw_response}\nUser: There was an error. Please check your function call format and JSON payload."

                    elif action_line.startswith("FINAL_ANSWER:"):
                        final_answer = action_line.split(":", 1)[1].strip()
                        console.print(Panel(f"Final Diagnosis: {final_answer}", title="Conclusion", border_style="green"))
                        break
                    
                    elif action_line.startswith("REQUEST_CORRECTION:"):
                        correction_request = action_line.split(":", 1)[1].strip()
                        console.print(Panel(f"Correction Request: {correction_request}", title="User Action Required", border_style="red"))
                        # In a real scenario, you might prompt the user for input here.
                        # For this simulation, we'll just stop.
                        break
                        
                    else:
                        # The model might have only returned reasoning, so we prompt it to continue.
                        prompt += f"\nAssistant: {raw_response}\nUser: Please proceed with the next action (`FUNCTION_CALL`, `FINAL_ANSWER`, etc.)."

                problem = """A patient presents at a clinic. 
                The three most likely diseases are 'Viral Infection', 'Bacterial Infection', or 'Allergies'. 
                The base rates (priors) for these in the population are 60%, 30%, and 10% respectively. 
                The patient reports having a 'High Fever'. 
                The probability of a high fever given a viral infection is 70%, given a bacterial infection is 85%, and given allergies is 5%. 
                Next, the patient reports 'Sneezing'. The probability of sneezing given a viral infection is 50%, given a bacterial infection is 20%, and for allergies is 90%. 
                Determine the most likely diagnosis."""
                
                console.print(Panel(f"Problem: {problem}", border_style="purple"))

                prompt = f"{system_prompt}\n\nUser: {problem}"
                
                for _ in range(10): # Increased turn limit for more complex reasoning
                    response = await generate_with_timeout(client, prompt)
                    if not response or not response.text:
                        console.print("[red]No response from LLM.[/red]")
                        break

                    # Handle multi-line responses (Reasoning + Action)
                    raw_response = response.text.strip()
                    console.print(f"\n[yellow]Assistant:[/yellow]\n{raw_response}")
                    
                    # The action is the last line of the response
                    action_line = raw_response.splitlines()[-1].strip().strip('`')

                    if action_line.startswith("FUNCTION_CALL:"):
                        _, function_info = action_line.split(":", 1)
                        parts = function_info.split("|")
                        func_name = parts[0].strip().replace("()", "")
                        
                        try:
                            # Handle calls with no arguments
                            if func_name == "get_current_diagnosis":
                                tool_result = await session.call_tool(func_name)
                                prompt += f"\nAssistant: {raw_response}\nUser: The current diagnosis is {tool_result.content[0].text}. What is your conclusion?"
                                continue

                            # Handle calls with arguments
                            if len(parts) < 2:
                                raise ValueError("Function call is missing arguments.")

                            payload_str = parts[1].strip()
                            payload = json.loads(payload_str)

                            if func_name == "initialize_beliefs":
                                tool_result = await session.call_tool(func_name, arguments={"priors": payload})
                                prompt += f"\nAssistant: {raw_response}\nUser: Beliefs initialized. Now consider the first symptom."
                            
                            elif func_name == "update_belief_with_evidence":
                                evidence = payload.get("evidence")
                                likelihoods = payload.get("likelihoods")
                                tool_result = await session.call_tool(func_name, arguments={"evidence": evidence, "likelihoods": likelihoods})
                                prompt += f"\nAssistant: {raw_response}\nUser: Beliefs updated. Now consider the next symptom or finalize the diagnosis."

                        except Exception as e:
                            console.print(f"[red]Error processing tool call: {e}[/red]")
                            prompt += f"\nAssistant: {raw_response}\nUser: There was an error. Please check your function call format and JSON payload."

                    elif action_line.startswith("FINAL_ANSWER:"):
                        final_answer = action_line.split(":", 1)[1].strip()
                        console.print(Panel(f"Final Diagnosis: {final_answer}", title="Conclusion", border_style="green"))
                        break
                    
                    elif action_line.startswith("REQUEST_CORRECTION:"):
                        correction_request = action_line.split(":", 1)[1].strip()
                        console.print(Panel(f"Correction Request: {correction_request}", title="User Action Required", border_style="red"))
                        # In a real scenario, you might prompt the user for input here.
                        # For this simulation, we'll just stop.
                        break
                        
                    else:
                        # The model might have only returned reasoning, so we prompt it to continue.
                        prompt += f"\nAssistant: {raw_response}\nUser: Please proceed with the next action (`FUNCTION_CALL`, `FINAL_ANSWER`, etc.)."

                console.print("\n[green]Diagnosis complete![/green]")

    except Exception as e:
        console.print(f"[red]An unexpected error occurred: {e}[/red]")

if __name__ == "__main__":
    asyncio.run(main())
