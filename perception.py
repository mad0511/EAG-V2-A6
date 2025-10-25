import logging
from models import DiagnosticInput, UserPreferences
from typing import Optional, Dict, Set, List
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()

from formatting import print_layer_header, print_layer_output, print_separator

from medical_knowledge import DISEASE_CATEGORIES
import re

class PerceptionLayer:
    """
    Perception Layer - Processes raw input into structured diagnostic information.
    - Validates and structures user input
    - Applies user preferences to input processing
    - Extracts relevant diagnostic information
    """
    
    def __init__(self, user_preferences: UserPreferences):
        self.preferences = user_preferences
        self.known_symptoms = set()
        for category in DISEASE_CATEGORIES.values():
            self.known_symptoms.update(category["symptoms"])
        logger.info(f"Initialized Perception Layer with preferences for user: {user_preferences.name}")

    def process_input(self, raw_description: str, diagnostic_input: DiagnosticInput) -> DiagnosticInput:
        """Process raw input into structured diagnostic input"""
        print_separator()
        print_layer_header("PERCEPTION LAYER")
        console.print("Extracting facts from input...")
        
        # Extract symptoms from the description
        detected_symptoms = self._extract_symptoms(raw_description.lower())
        
        # Update diagnostic input with detected symptoms
        diagnostic_input.symptoms = detected_symptoms
        
        # Apply user preferences and add context
        diagnostic_input = self.adapt_to_preferences(diagnostic_input)
        
        # Add context about symptom severity if high
        if diagnostic_input.severity >= 7:
            high_severity_context = "High severity symptoms detected"
            if diagnostic_input.additional_context:
                diagnostic_input.additional_context += f"\n{high_severity_context}"
            else:
                diagnostic_input.additional_context = high_severity_context
        
        # Display structured output
        output_dict = {
            "Original Description": raw_description,
            "Detected Symptoms": ", ".join(detected_symptoms) if detected_symptoms else "None detected",
            "Severity": f"{diagnostic_input.severity}/10" if diagnostic_input.severity else "Not rated",
            "Duration": diagnostic_input.duration or "Not specified"
        }
        
        if diagnostic_input.additional_context:
            output_dict["Context"] = diagnostic_input.additional_context
        
        print_layer_output({"Perception Output": output_dict})
        
        # Log processing results
        logger.info(f"Processed input with severity {diagnostic_input.severity}, detected {len(detected_symptoms)} symptoms")
        return diagnostic_input
        
    def _extract_symptoms(self, text: str) -> Set[str]:
        """Extract known symptoms from text description."""
        detected = set()
        
        # Check for temperature values
        temp_pattern = r'(?:temperature|temp|fever)[^\d]*(\d+\.?\d*)'
        temp_match = re.search(temp_pattern, text, re.IGNORECASE)
        if temp_match:
            try:
                temp = float(temp_match.group(1))
                if temp > 98.6:  # Fahrenheit
                    detected.add("fever")
                    detected.add("high temperature")
                elif temp > 37:  # Celsius
                    detected.add("fever")
                    detected.add("high temperature")
            except ValueError:
                pass  # Invalid temperature format
        
        # Check for known symptoms
        for symptom in self.known_symptoms:
            if symptom in text:
                detected.add(symptom)
            # Check for common variations
            variations = self._get_symptom_variations(symptom)
            if any(var in text for var in variations):
                detected.add(symptom)
        return detected
    
    def _get_symptom_variations(self, symptom: str) -> List[str]:
        """Generate common variations of symptom descriptions."""
        variations = [symptom]
        
        # Special case variations with severity indicators
        special_cases = {
            "nausea": ["nauseous", "nauseated", "feeling sick", "queasy", "sick to stomach"],
            "fever": ["high temperature", "elevated temperature", "temperature", "hot", "feverish", "running a fever"],
            "headache": ["head pain", "head ache", "migraine", "pounding head", "throbbing headache"],
            "cough": ["coughing", "persistent cough", "dry cough", "chest cough", "hacking"]
        }
        
        # Severity modifiers that strengthen symptom detection
        severity_modifiers = {
            "fever": ["high", "severe", "very", "extreme"],
            "headache": ["severe", "bad", "terrible", "intense"],
            "cough": ["bad", "severe", "constant", "persistent"],
            "nausea": ["severe", "intense", "extreme", "constant"]
        }
        
        if symptom in special_cases:
            variations.extend(special_cases[symptom])
        
        # Handle plural/singular
        if symptom.endswith('s'):
            variations.append(symptom[:-1])
        else:
            variations.append(symptom + 's')
            
        # Handle common prefixes
        prefixes = ['severe ', 'mild ', 'chronic ', 'acute ', 'feeling ']
        variations.extend(prefix + var for prefix in prefixes for var in variations[:])
        
        return variations

        # Display structured output
        print_layer_output({
            "Perception Output": {
                "Original Description": raw_description,
                "Detected Symptoms": ", ".join(detected_symptoms) if detected_symptoms else "None detected",
                "Severity": f"{severity}/10",
                "Duration": duration,
                "Context": context or "None provided"
            }
        })
        
        logger.info(f"Processed input with severity {severity}, detected {len(detected_symptoms)} symptoms")
        return diagnostic_input

    def adapt_to_preferences(self, input_data: DiagnosticInput) -> DiagnosticInput:
        """Adjust input processing based on user preferences"""
        logger.debug("Adapting input to user preferences")
        
        contexts = []
        
        # Check for health concerns in symptoms
        for concern in self.preferences.primary_health_concerns:
            matching_symptoms = self._get_matching_symptoms_for_category(concern, input_data.symptoms)
            if matching_symptoms:
                contexts.append(f"Symptoms match {concern.lower()} concerns: {', '.join(matching_symptoms)}")
                logger.info(f"Input matches user's health concern: {concern}")
        
        # Add medical history context if relevant
        relevant_history = self._check_medical_history_relevance(input_data.symptoms)
        if relevant_history:
            contexts.append(f"Related to medical history: {', '.join(relevant_history)}")
        
        # Add age-related context
        if input_data.age > 60 and input_data.severity >= 7:
            contexts.append("Note: Age may increase risk factors")
        
        # Combine all context information
        if contexts:
            context_str = "\n".join(contexts)
            if input_data.additional_context:
                input_data.additional_context += f"\n{context_str}"
            else:
                input_data.additional_context = context_str
                
        return input_data
        
    def _get_matching_symptoms_for_category(self, category: str, symptoms: Set[str]) -> Set[str]:
        """Find symptoms that match a specific health category"""
        if category in DISEASE_CATEGORIES:
            category_symptoms = DISEASE_CATEGORIES[category]["symptoms"]
            return symptoms.intersection(category_symptoms)
        return set()
        
    def _check_medical_history_relevance(self, symptoms: Set[str]) -> List[str]:
        """Check if current symptoms relate to medical history"""
        relevant_conditions = []
        for condition in self.preferences.medical_history:
            # Check if condition exists in any category's conditions
            for category in DISEASE_CATEGORIES.values():
                if condition in category["conditions"]:
                    # If condition's category has overlapping symptoms
                    if symptoms.intersection(category["symptoms"]):
                        relevant_conditions.append(condition)
                        break
        return relevant_conditions