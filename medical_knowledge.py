from typing import Dict, List, Set

# Disease categories and their associated conditions
DISEASE_CATEGORIES = {
    "Infectious": {
        "conditions": {
            "Common Cold": 0.0,
            "Flu": 0.0,
            "Viral Infection": 0.0,
            "Bacterial Infection": 0.0,
            "COVID-19": 0.0
        },
        "symptoms": {
            "fever", "high temperature", "cough", "sore throat", 
            "runny nose", "congestion", "body aches", "fatigue",
            "nausea", "vomiting", "headache", "chills"
        }
    },
    "Cardiovascular": {
        "conditions": {
            "Hypertension": 0.0,
            "Coronary Artery Disease": 0.0,
            "Heart Failure": 0.0,
            "Arrhythmia": 0.0,
            "Deep Vein Thrombosis": 0.0
        },
        "symptoms": {
            "chest pain", "shortness of breath", "irregular heartbeat", 
            "swelling in legs", "fatigue", "dizziness", "high blood pressure",
            "rapid heartbeat", "leg pain", "leg swelling"
        }
    },
    "Diabetes": {
        "conditions": {
            "Type 1 Diabetes": 0.0,
            "Type 2 Diabetes": 0.0,
            "Diabetic Neuropathy": 0.0,
            "Diabetic Retinopathy": 0.0,
            "Hypoglycemia": 0.0,
            "Hyperglycemia": 0.0
        },
        "symptoms": {
            "excessive thirst", "frequent urination", "unexplained weight loss",
            "blurred vision", "slow healing", "numbness in hands/feet",
            "increased hunger", "fatigue", "dry skin", "high blood sugar",
            "sudden weight loss", "mood changes", "bedwetting in children",
            "rapid breathing", "fruity breath odor"
        }
    },
    "Respiratory": {
        "conditions": {
            "Asthma": 0.0,
            "COPD": 0.0,
            "Bronchitis": 0.0,
            "Pneumonia": 0.0,
            "Pulmonary Embolism": 0.0
        },
        "symptoms": {
            "shortness of breath", "wheezing", "chronic cough", 
            "chest tightness", "difficulty breathing", "coughing up mucus",
            "rapid breathing", "chest pain", "blue lips or fingers"
        }
    },
    "Digestive": {
        "conditions": {
            "GERD": 0.0,
            "Gastritis": 0.0,
            "Peptic Ulcer": 0.0,
            "IBS": 0.0,
            "Gallstones": 0.0
        },
        "symptoms": {
            "abdominal pain", "heartburn", "nausea", "vomiting",
            "bloating", "changes in bowel movements", "stomach pain",
            "acid reflux", "loss of appetite", "indigestion", 
            "difficulty swallowing", "difficulty eating", "chest pain",
            "burning sensation", "regurgitation", "acidity"
        }
    },
    "Musculoskeletal": {
        "conditions": {
            "Osteoarthritis": 0.0,
            "Rheumatoid Arthritis": 0.0,
            "Fibromyalgia": 0.0,
            "Osteoporosis": 0.0,
            "Lower Back Pain": 0.0
        },
        "symptoms": {
            "joint pain", "muscle pain", "stiffness", "swelling in joints",
            "reduced mobility", "back pain", "neck pain", "weakness",
            "limited range of motion", "muscle weakness"
        }
    }
}

# Condition details with descriptions and risk factors
CONDITION_DETAILS = {
    "Type 1 Diabetes": {
        "description": "An autoimmune condition where the body doesn't produce insulin.",
        "common_symptoms": "Excessive thirst, frequent urination, sudden weight loss, increased hunger",
        "risk_factors": "Family history, young age, certain genes, geography",
        "emergency_symptoms": {"diabetic ketoacidosis", "severe dehydration", "confusion", "fruity breath"},
        "age_risk": lambda age: 1.3 if age < 30 else 1.0,
        "symptom_weights": {
            "excessive thirst": 2.0,
            "frequent urination": 2.0,
            "sudden weight loss": 1.8,
            "increased hunger": 1.5,
            "fatigue": 1.2,
            "blurred vision": 1.2,
            "mood changes": 1.1,
            "bedwetting in children": 1.4,
            "fruity breath odor": 1.8,
            "rapid breathing": 1.5
        }
    },
    "GERD": {
        "description": "Gastroesophageal reflux disease - chronic acid reflux condition.",
        "common_symptoms": "Heartburn, acid reflux, difficulty swallowing, chest pain",
        "risk_factors": "Obesity, pregnancy, smoking, certain foods",
        "emergency_symptoms": {"severe chest pain", "difficulty breathing", "vomiting blood"},
        "age_risk": lambda age: 1.2 if age > 40 else 1.0,
        "symptom_weights": {
            "heartburn": 2.0,        # Primary symptom
            "acid reflux": 2.0,      # Primary symptom
            "chest pain": 1.5,
            "difficulty eating": 1.3,
            "burning sensation": 1.5,
            "regurgitation": 1.4,
            "acidity": 1.5
        }
    },
    "Gastritis": {
        "description": "Inflammation of the stomach lining.",
        "common_symptoms": "Stomach pain, nausea, indigestion, loss of appetite",
        "risk_factors": "H. pylori infection, NSAIDs use, alcohol",
        "emergency_symptoms": {"severe abdominal pain", "bloody vomit", "dark stools"},
        "age_risk": lambda age: 1.0,
        "symptom_weights": {
            "stomach pain": 1.8,
            "nausea": 1.4,
            "indigestion": 1.3,
            "loss of appetite": 1.2,
            "heartburn": 1.0,
            "acid reflux": 0.8
        }
    },
    "Flu": {
        "description": "An influenza viral infection with more severe symptoms than a cold.",
        "common_symptoms": "High fever, body aches, fatigue, cough, nausea",
        "risk_factors": "Season (winter), close contact with infected people",
        "emergency_symptoms": {"difficulty breathing", "chest pain", "severe fever", "confusion"},
        "age_risk": lambda age: 1.2 if age > 65 or age < 5 else 1.0,
        "symptom_weights": {
            "fever": 1.5,  # High fever is common
            "cough": 1.2,
            "headache": 1.3,
            "nausea": 1.0  # More common in flu
        }
    },
    "Viral Infection": {
        "description": "A general viral infection of the body.",
        "common_symptoms": "Fever, fatigue, body aches, nausea",
        "risk_factors": "Weakened immune system, exposure to viruses",
        "emergency_symptoms": {"severe fever", "difficulty breathing", "severe dehydration"},
        "age_risk": lambda age: 1.1 if age > 60 or age < 10 else 1.0,
        "symptom_weights": {
            "fever": 1.3,
            "cough": 0.8,
            "headache": 1.2,
            "nausea": 1.1
        }
    },
    "COVID-19": {
        "description": "A coronavirus infection affecting multiple body systems.",
        "common_symptoms": "Fever, cough, fatigue, loss of taste/smell",
        "risk_factors": "Close contact, poor ventilation, crowded spaces",
        "emergency_symptoms": {"severe breathing difficulty", "chest pain", "confusion"},
        "age_risk": lambda age: 1.3 if age > 60 or age < 12 else 1.0,
        "symptom_weights": {
            "fever": 1.4,
            "cough": 1.5,
            "headache": 1.1,
            "nausea": 0.8
        }
    }
}

def get_related_conditions(symptoms: Set[str]) -> Dict[str, float]:
    """Get conditions related to given symptoms with initial probabilities."""
    related_conditions = {}
    
    # Count symptom matches for each category
    for category, data in DISEASE_CATEGORIES.items():
        symptom_overlap = len(data["symptoms"].intersection(symptoms))
        if symptom_overlap > 0:
            # Calculate base probability based on symptom overlap
            base_prob = symptom_overlap / len(data["symptoms"])
            # Add conditions from matching categories
            for condition in data["conditions"]:
                related_conditions[condition] = base_prob
    
    return related_conditions

def adjust_probabilities_for_age(conditions: Dict[str, float], age: int) -> Dict[str, float]:
    """Adjust condition probabilities based on age."""
    adjusted = {}
    for condition, prob in conditions.items():
        if condition in CONDITION_DETAILS:
            age_factor = CONDITION_DETAILS[condition]["age_risk"](age)
            adjusted[condition] = prob * age_factor
        else:
            adjusted[condition] = prob
    
    # Normalize probabilities
    total = sum(adjusted.values())
    if total > 0:
        return {k: v/total for k, v in adjusted.items()}
    return adjusted

def check_emergency_symptoms(symptoms: Set[str], conditions: List[str]) -> List[str]:
    """Check if any symptoms are considered emergency symptoms for the conditions."""
    emergency_warnings = []
    
    for condition in conditions:
        if condition in CONDITION_DETAILS:
            condition_data = CONDITION_DETAILS[condition]
            if "emergency_symptoms" in condition_data:
                emergency_matches = condition_data["emergency_symptoms"].intersection(symptoms)
                if emergency_matches:
                    emergency_warnings.append(
                        f"Warning: {condition} - Emergency symptoms detected: {', '.join(emergency_matches)}"
                    )
    
    return emergency_warnings