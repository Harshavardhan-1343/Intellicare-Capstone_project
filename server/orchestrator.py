import requests
import json
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import pickle

@dataclass
class PatientProfile:
    """Patient information collected during conversation"""
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    symptoms: List[str] = None
    duration: Optional[str] = None
    severity: Optional[str] = None
    medications: List[str] = None
    medical_history: List[str] = None
    recent_travel: bool = False
    dietary_changes: bool = False
    fever: bool = False
    
    def __post_init__(self):
        if self.symptoms is None:
            self.symptoms = []
        if self.medications is None:
            self.medications = []
        if self.medical_history is None:
            self.medical_history = []
    
    def to_dict(self):
        return asdict(self)


class OllamaClient:
    """Ollama API client for MedLlama2"""
    
    def __init__(self, model_name="medllama2", base_url="http://localhost:11434"):
        self.model_name = model_name
        self.api_url = f"{base_url}/api/generate"
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Ollama is running"""
        try:
            response = self.generate("test", max_tokens=5)
            print(f"✓ Connected to Ollama ({self.model_name})")
        except:
            raise ConnectionError(
                "Cannot connect to Ollama. Please run: ollama serve\n"
                f"And ensure model is available: ollama pull {self.model_name}"
            )
    
    def generate(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> str:
        """Generate text from MedLlama2"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "stop": ["\n\n", "User:", "Patient:"]  # Stop at conversation breaks
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=45)
            response.raise_for_status()
            return response.json()["response"].strip()
        except requests.exceptions.Timeout:
            return "I apologize, I need a moment. Could you please repeat that?"
        except Exception as e:
            print(f"Ollama error: {e}")
            return ""


class SymptomExtractor:
    """Extract and validate symptoms from patient responses"""
    
    SYMPTOM_DATABASE = {
        # Respiratory
        'cough', 'shortness of breath', 'wheezing', 'chest pain', 'sore throat',
        'runny nose', 'congestion', 'sneezing',
        
        # Gastrointestinal
        'nausea', 'vomiting', 'diarrhea', 'constipation', 'abdominal pain',
        'bloating', 'loss of appetite', 'heartburn',
        
        # Pain
        'headache', 'back pain', 'joint pain', 'muscle pain', 'neck pain',
        
        # Systemic
        'fever', 'chills', 'fatigue', 'weakness', 'sweating', 'weight loss',
        'dizziness', 'fainting',
        
        # Neurological
        'confusion', 'numbness', 'tingling', 'vision changes', 'hearing loss',
        'seizures', 'tremors',
        
        # Skin
        'rash', 'itching', 'swelling', 'bruising', 'pale skin',
        
        # Cardiovascular
        'palpitations', 'irregular heartbeat', 'chest pressure',
    }
    
    def extract(self, text: str) -> List[str]:
        """Extract symptoms from text"""
        text_lower = text.lower()
        found = []
        
        # Direct matching
        for symptom in self.SYMPTOM_DATABASE:
            if symptom in text_lower:
                found.append(symptom)
        
        # Common variations
        variations = {
            'stomach pain': 'abdominal pain',
            'throwing up': 'vomiting',
            'upset stomach': 'nausea',
            'temperature': 'fever',
            'hot': 'fever',
            'tired': 'fatigue',
            'dizzy': 'dizziness',
        }
        
        for variant, canonical in variations.items():
            if variant in text_lower and canonical not in found:
                found.append(canonical)
        
        return list(set(found))


class ConversationState:
    """Tracks conversation state and what information is needed"""
    
    REQUIRED_INFO = [
        'age',
        'primary_symptoms',
        'symptom_duration',
        'symptom_severity',
        'recent_travel',
        'medications',
        'medical_history',
        'dietary_changes'
    ]
    
    def __init__(self):
        self.collected = set()
        self.turn_count = 0
        self.max_turns = 12  # Maximum questions before forcing diagnosis
    
    def mark_collected(self, info_type: str):
        """Mark information as collected"""
        self.collected.add(info_type)
    
    def is_complete(self) -> bool:
        """Check if we have enough information"""
        # Must have at least these
        critical = {'age', 'primary_symptoms', 'symptom_duration'}
        has_critical = critical.issubset(self.collected)
        
        # Either have all info, or reached turn limit with minimum info
        return (
            has_critical and len(self.collected) >= 6
        ) or (
            self.turn_count >= self.max_turns and has_critical
        )
    
    def get_missing_info(self) -> List[str]:
        """Get list of missing required information"""
        return [info for info in self.REQUIRED_INFO if info not in self.collected]


class QuestionGenerator:
    """Generate appropriate questions based on conversation state"""
    
    QUESTION_TEMPLATES = {
        'greeting': [
            "Hello! I'm here to help assess your symptoms. What brings you here today?",
        ],
        'age': [
            "May I ask your age?",
            "How old are you?",
        ],
        'primary_symptoms': [
            "What symptoms are you experiencing?",
            "Can you describe what you're feeling?",
        ],
        'symptom_duration': [
            "How long have you been experiencing these symptoms?",
            "When did these symptoms start?",
        ],
        'symptom_severity': [
            "On a scale of 1-10, how severe would you rate your symptoms?",
            "How much are these symptoms affecting your daily activities?",
        ],
        'recent_travel': [
            "Have you traveled anywhere recently, either internationally or domestically?",
            "Any recent trips or travels?",
        ],
        'medications': [
            "Have you taken any medication for these symptoms?",
            "Are you currently taking any medications?",
        ],
        'medical_history': [
            "Do you have any known medical conditions or chronic illnesses?",
            "Any previous medical history we should know about?",
        ],
        'dietary_changes': [
            "Have you eaten anything unusual or outside your normal diet recently?",
            "Any changes in your eating habits lately?",
        ],
        'pain_specific': [
            "Can you describe the type of pain? Is it sharp, dull, throbbing, or burning?",
            "Does the pain stay in one place or does it radiate?",
            "What makes the pain better or worse?",
        ],
        'fever_check': [
            "Do you have a fever? Have you measured your temperature?",
        ],
        'breathing_check': [
            "Are you having any difficulty breathing?",
        ],
        'additional': [
            "Is there anything else you think I should know?",
            "Any other symptoms or concerns?",
        ]
    }
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    def generate_question(
        self, 
        state: ConversationState, 
        patient: PatientProfile,
        last_response: str = ""
    ) -> str:
        """Generate the next appropriate question"""
        
        # Greeting
        if state.turn_count == 0:
            return self.QUESTION_TEMPLATES['greeting'][0]
        
        # Get missing info
        missing = state.get_missing_info()
        
        if not missing:
            return None  # Ready to diagnose
        
        # Prioritize critical information
        priority_order = [
            'primary_symptoms',
            'age', 
            'symptom_duration',
            'symptom_severity',
            'medications',
            'recent_travel',
            'medical_history',
            'dietary_changes'
        ]
        
        # Find next question to ask
        next_topic = None
        for topic in priority_order:
            if topic in missing:
                next_topic = topic
                break
        
        if not next_topic and missing:
            next_topic = missing[0]
        
        # Special case: if pain symptoms, ask pain-specific questions
        if any('pain' in s for s in patient.symptoms) and state.turn_count <= 8:
            if 'pain_details' not in state.collected:
                state.mark_collected('pain_details')
                return self._naturalize_question(
                    self.QUESTION_TEMPLATES['pain_specific'][0],
                    last_response
                )
        
        # Get template question
        templates = self.QUESTION_TEMPLATES.get(next_topic, ['Could you tell me more?'])
        base_question = templates[0]
        
        # Naturalize the question using LLM
        return self._naturalize_question(base_question, last_response)
    
    def _naturalize_question(self, question: str, last_response: str) -> str:
        """Use MedLlama2 to make question sound more natural"""
        
        if not last_response or len(last_response) < 5:
            return question
        
        # Create prompt for natural transition
        prompt = f"""You are a medical assistant. The patient just said: "{last_response}"

Give a brief empathetic acknowledgment (1 short sentence), then ask: "{question}"

Keep it conversational and caring. Response:"""
        
        response = self.ollama.generate(prompt, max_tokens=80, temperature=0.7)
        
        # Fallback if generation fails or is too long
        if not response or len(response) < 10 or len(response) > 200:
            return f"I understand. {question}"
        
        # Clean up response
        response = response.strip()
        
        # Ensure it ends with question mark
        if not response.endswith('?'):
            response = f"{response.rstrip('.')}?"
        
        return response


class InformationParser:
    """Parse patient responses to extract structured information"""
    
    def __init__(self, symptom_extractor: SymptomExtractor):
        self.symptom_extractor = symptom_extractor
    
    def parse_response(
        self, 
        text: str, 
        expected_info: str,
        patient: PatientProfile
    ) -> bool:
        """Parse response and update patient profile. Returns True if info extracted."""
        
        text_lower = text.lower()
        
        if expected_info == 'age':
            age = self._extract_age(text)
            if age:
                patient.age = age
                return True
        
        elif expected_info == 'primary_symptoms':
            symptoms = self.symptom_extractor.extract(text)
            if symptoms:
                patient.symptoms.extend(symptoms)
                patient.symptoms = list(set(patient.symptoms))
                return True
        
        elif expected_info == 'symptom_duration':
            duration = self._extract_duration(text)
            if duration:
                patient.duration = duration
                return True
        
        elif expected_info == 'symptom_severity':
            severity = self._extract_severity(text)
            if severity:
                patient.severity = severity
                return True
        
        elif expected_info == 'recent_travel':
            patient.recent_travel = any(word in text_lower for word in ['yes', 'yeah', 'travelled', 'trip', 'went to'])
            return True
        
        elif expected_info == 'medications':
            if 'no' not in text_lower or any(med in text_lower for med in ['aspirin', 'ibuprofen', 'tylenol', 'paracetamol']):
                patient.medications.append(text)
            return True
        
        elif expected_info == 'medical_history':
            if 'no' not in text_lower:
                patient.medical_history.append(text)
            return True
        
        elif expected_info == 'dietary_changes':
            patient.dietary_changes = any(word in text_lower for word in ['yes', 'yeah', 'maybe', 'ate'])
            return True
        
        # Always try to extract symptoms from any response
        symptoms = self.symptom_extractor.extract(text)
        if symptoms:
            patient.symptoms.extend(symptoms)
            patient.symptoms = list(set(patient.symptoms))
        
        return False
    
    def _extract_age(self, text: str) -> Optional[int]:
        """Extract age from text"""
        # Look for numbers
        numbers = re.findall(r'\b(\d{1,3})\b', text)
        for num in numbers:
            age = int(num)
            if 0 < age < 120:
                return age
        return None
    
    def _extract_duration(self, text: str) -> Optional[str]:
        """Extract duration from text"""
        text_lower = text.lower()
        
        # Pattern matching
        patterns = [
            (r'(\d+)\s*days?', 'days'),
            (r'(\d+)\s*weeks?', 'weeks'),
            (r'(\d+)\s*months?', 'months'),
            (r'(\d+)\s*hours?', 'hours'),
        ]
        
        for pattern, unit in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return f"{match.group(1)} {unit}"
        
        # Relative terms
        if 'yesterday' in text_lower or 'today' in text_lower:
            return '1 day'
        if 'week' in text_lower:
            return '1 week'
        
        return text[:50] if len(text) < 50 else None
    
    def _extract_severity(self, text: str) -> Optional[str]:
        """Extract severity from text"""
        text_lower = text.lower()
        
        # Numeric scale
        numbers = re.findall(r'\b(\d{1,2})\b', text)
        for num in numbers:
            score = int(num)
            if 1 <= score <= 10:
                if score <= 3:
                    return f"mild ({score}/10)"
                elif score <= 6:
                    return f"moderate ({score}/10)"
                else:
                    return f"severe ({score}/10)"
        
        # Descriptive terms
        if any(word in text_lower for word in ['severe', 'extreme', 'unbearable', 'worst']):
            return 'severe'
        if any(word in text_lower for word in ['moderate', 'manageable', 'noticeable']):
            return 'moderate'
        if any(word in text_lower for word in ['mild', 'slight', 'minor', 'little']):
            return 'mild'
        
        return None


class DiagnosisEngine:
    """Generate diagnosis using MedLlama2"""
    
    TRIAGE_CRITERIA = {
        1: {  # Immediate emergency
            'keywords': ['chest pain', 'difficulty breathing', 'severe bleeding', 
                        'loss of consciousness', 'stroke', 'heart attack', 'severe trauma'],
            'severity_min': 9
        },
        2: {  # Emergency
            'keywords': ['severe pain', 'high fever', 'confusion', 'significant bleeding',
                        'suspected fracture', 'severe allergic reaction'],
            'severity_min': 7
        },
        3: {  # Urgent
            'keywords': ['persistent fever', 'significant pain', 'infection signs',
                        'persistent vomiting', 'dehydration'],
            'severity_min': 5
        },
        4: {  # Semi-urgent
            'keywords': ['moderate pain', 'persistent symptoms', 'minor infection'],
            'severity_min': 3
        },
        5: {  # Non-urgent
            'keywords': ['mild symptoms', 'chronic condition management'],
            'severity_min': 0
        }
    }
    
    DEPARTMENT_ROUTING = {
        'Emergency Medicine': ['severe', 'acute', 'trauma', 'immediate', 'emergency', 'life-threatening'],
        'Cardiology': ['chest pain', 'heart', 'palpitation', 'cardiac', 'angina', 'hypertension'],
        'Pulmonology': ['breathing', 'cough', 'lung', 'respiratory', 'asthma', 'pneumonia'],
        'Gastroenterology': ['abdominal pain', 'nausea', 'vomiting', 'diarrhea', 'stomach', 'liver'],
        'Neurology': ['headache', 'migraine', 'numbness', 'seizure', 'stroke', 'confusion', 'dizziness'],
        'Orthopedics': ['bone', 'joint pain', 'fracture', 'sprain', 'back pain', 'arthritis'],
        'Dermatology': ['rash', 'itching', 'skin', 'swelling', 'lesion'],
        'ENT': ['sore throat', 'ear pain', 'hearing', 'runny nose', 'sinus'],
        'Infectious Disease': ['fever', 'infection', 'sepsis'],
        'General Medicine': []  # Default
    }
    
    def __init__(self, ollama_client: OllamaClient):
        """Initialize diagnosis engine with Ollama client"""
        self.ollama = ollama_client
        print("✓ Diagnosis engine initialized (using MedLlama2)")
    
    def diagnose(self, patient: PatientProfile) -> Dict:
        """Generate complete diagnosis using MedLlama2"""
        
        print("\n[Analyzing patient data with MedLlama2...]")
        
        # Get disease predictions from MedLlama2
        diagnoses = self._get_llm_diagnosis(patient)
        
        # Calculate triage level
        triage_level = self._calculate_triage(patient, diagnoses)
        
        # Route to department
        department = self._route_department(patient, diagnoses)
        
        # Get triage message
        triage_message = self._get_triage_message(triage_level)
        
        return {
            'diagnoses': diagnoses,
            'triage_level': triage_level,
            'triage_message': triage_message,
            'department': department,
            'patient_profile': patient.to_dict()
        }
    
    def _get_llm_diagnosis(self, patient: PatientProfile) -> List[Dict]:
        """Use MedLlama2 to generate diagnosis"""
        
        # Create comprehensive medical prompt
        prompt = self._create_diagnosis_prompt(patient)
        
        # Get response from MedLlama2
        response = self.ollama.generate(prompt, max_tokens=500, temperature=0.3)
        
        # Parse the response
        diagnoses = self._parse_diagnosis_response(response)
        
        # Fallback if parsing fails
        if not diagnoses or len(diagnoses) == 0:
            diagnoses = self._fallback_diagnosis(patient)
        
        return diagnoses[:3]  # Top 3
    
    def _create_diagnosis_prompt(self, patient: PatientProfile) -> str:
        """Create structured prompt for diagnosis"""
        
        prompt = """You are an experienced medical doctor. Based on the patient information below, provide the top 3 most likely differential diagnoses.

PATIENT INFORMATION:
"""
        
        # Patient demographics
        if patient.age:
            prompt += f"Age: {patient.age} years\n"
        if patient.gender:
            prompt += f"Gender: {patient.gender}\n"
        
        # Chief complaints
        if patient.symptoms:
            prompt += f"\nChief Complaints:\n"
            for symptom in patient.symptoms:
                prompt += f"  - {symptom}\n"
        
        # Clinical details
        if patient.duration:
            prompt += f"\nDuration: {patient.duration}\n"
        
        if patient.severity:
            prompt += f"Severity: {patient.severity}\n"
        
        # Medical history
        if patient.medical_history and any(patient.medical_history):
            prompt += f"\nMedical History:\n"
            for item in patient.medical_history:
                if item and item.lower() not in ['no', 'none', 'nothing']:
                    prompt += f"  - {item}\n"
        
        # Current medications
        if patient.medications and any(patient.medications):
            prompt += f"\nCurrent Medications:\n"
            for med in patient.medications:
                if med and med.lower() not in ['no', 'none']:
                    prompt += f"  - {med}\n"
        
        # Risk factors
        if patient.recent_travel:
            prompt += f"\nRecent Travel: Yes\n"
        
        if patient.dietary_changes:
            prompt += f"Dietary Changes: Yes\n"
        
        # Request structured output
        prompt += """
TASK: Provide exactly 3 differential diagnoses in this exact format:

1. [Disease Name] - [Probability percentage]% - Brief explanation (1-2 sentences)
2. [Disease Name] - [Probability percentage]% - Brief explanation (1-2 sentences)
3. [Disease Name] - [Probability percentage]% - Brief explanation (1-2 sentences)

Guidelines:
- List from most likely to least likely
- Probability should be realistic (don't use 100%)
- Consider age, symptoms, duration, and severity
- Provide actual medical differential diagnoses
- Keep explanations brief and clinical

Your diagnosis:"""
        
        return prompt
    
    def _parse_diagnosis_response(self, response: str) -> List[Dict]:
        """Parse MedLlama2's diagnosis response"""
        
        diagnoses = []
        
        # Split into lines
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for numbered lines (1. 2. 3.)
            if re.match(r'^\d+\.\s', line):
                try:
                    # Remove number prefix
                    line = re.sub(r'^\d+\.\s*', '', line)
                    
                    # Try to extract disease name and probability
                    # Format: Disease Name - 75% - explanation
                    parts = line.split('-')
                    
                    if len(parts) >= 2:
                        disease_name = parts[0].strip()
                        
                        # Extract probability
                        prob_match = re.search(r'(\d+(?:\.\d+)?)\s*%', parts[1])
                        if prob_match:
                            probability = float(prob_match.group(1)) / 100
                        else:
                            # Default probability based on position
                            probability = 0.7 / (len(diagnoses) + 1)
                        
                        # Extract explanation if available
                        explanation = '-'.join(parts[2:]).strip() if len(parts) > 2 else parts[1].strip()
                        explanation = re.sub(r'\d+(?:\.\d+)?%', '', explanation).strip()
                        
                        # Determine confidence level
                        if probability >= 0.7:
                            confidence = 'high'
                        elif probability >= 0.4:
                            confidence = 'moderate'
                        else:
                            confidence = 'low'
                        
                        diagnoses.append({
                            'disease': disease_name,
                            'probability': probability,
                            'confidence': confidence,
                            'explanation': explanation[:200]  # Limit length
                        })
                
                except Exception as e:
                    print(f"Warning: Could not parse diagnosis line: {line} - {e}")
                    continue
        
        return diagnoses
    
    def _fallback_diagnosis(self, patient: PatientProfile) -> List[Dict]:
        """Fallback diagnosis if LLM parsing fails"""
        
        symptom_str = ' '.join(patient.symptoms).lower()
        diagnoses = []
        
        # Simple pattern matching
        patterns = {
            ('cough', 'fever'): {
                'disease': 'Upper Respiratory Infection',
                'probability': 0.75,
                'explanation': 'Common viral or bacterial infection presenting with respiratory symptoms'
            },
            ('headache', 'nausea'): {
                'disease': 'Migraine',
                'probability': 0.65,
                'explanation': 'Primary headache disorder with associated symptoms'
            },
            ('abdominal pain', 'nausea'): {
                'disease': 'Gastroenteritis',
                'probability': 0.70,
                'explanation': 'Inflammation of the digestive tract'
            },
            ('chest pain', 'shortness of breath'): {
                'disease': 'Possible Cardiac Event',
                'probability': 0.60,
                'explanation': 'Requires immediate medical evaluation'
            },
            ('fever', 'fatigue'): {
                'disease': 'Viral Infection',
                'probability': 0.70,
                'explanation': 'Common systemic viral illness'
            },
            ('back pain',): {
                'disease': 'Musculoskeletal Pain',
                'probability': 0.65,
                'explanation': 'Muscle strain or mechanical back pain'
            },
            ('dizziness', 'weakness'): {
                'disease': 'Orthostatic Hypotension',
                'probability': 0.55,
                'explanation': 'Drop in blood pressure upon standing'
            }
        }
        
        # Find matching patterns
        for symptoms, diag in patterns.items():
            if all(s in symptom_str for s in symptoms):
                diagnoses.append({
                    'disease': diag['disease'],
                    'probability': diag['probability'],
                    'confidence': 'moderate',
                    'explanation': diag['explanation']
                })
        
        # Add generic diagnoses if nothing matches
        if not diagnoses:
            diagnoses.append({
                'disease': 'Further Clinical Evaluation Needed',
                'probability': 0.0,
                'confidence': 'low',
                'explanation': 'Symptoms require in-person medical assessment for accurate diagnosis'
            })
        
        # Ensure we have 3 diagnoses
        generic_options = [
            {
                'disease': 'Viral Syndrome',
                'probability': 0.50,
                'confidence': 'moderate',
                'explanation': 'Non-specific viral illness with systemic symptoms'
            },
            {
                'disease': 'Stress-Related Symptoms',
                'probability': 0.40,
                'confidence': 'low',
                'explanation': 'Physical symptoms potentially related to psychological stress'
            },
            {
                'disease': 'Undifferentiated Illness',
                'probability': 0.30,
                'confidence': 'low',
                'explanation': 'Requires additional diagnostic workup'
            }
        ]
        
        while len(diagnoses) < 3:
            diagnoses.append(generic_options[len(diagnoses) - 1])
        
        return diagnoses[:3]
    
    def _calculate_triage(self, patient: PatientProfile, diagnoses: List[Dict]) -> int:
        """Calculate triage level (1=immediate, 5=routine)"""
        
        # Combine all text for analysis
        all_text = ' '.join(
            patient.symptoms + 
            [d['disease'] for d in diagnoses] +
            [d.get('explanation', '') for d in diagnoses]
        ).lower()
        
        # Check emergency keywords by level
        for level, criteria in self.TRIAGE_CRITERIA.items():
            if any(kw in all_text for kw in criteria['keywords']):
                return level
        
        # Severity-based triage
        if patient.severity:
            severity_str = patient.severity.lower()
            
            if 'severe' in severity_str:
                return 2
            
            # Extract numeric severity
            severity_match = re.search(r'(\d+)', patient.severity)
            if severity_match:
                score = int(severity_match.group(1))
                if score >= 9:
                    return 2
                elif score >= 7:
                    return 3
                elif score >= 5:
                    return 4
        
        # Check probabilities - high probability serious conditions
        serious_conditions = [
            'heart attack', 'stroke', 'pneumonia', 'appendicitis',
            'pulmonary embolism', 'sepsis', 'meningitis'
        ]
        
        for diag in diagnoses:
            if any(cond in diag['disease'].lower() for cond in serious_conditions):
                if diag['probability'] > 0.5:
                    return 2
                elif diag['probability'] > 0.3:
                    return 3
        
        return 5  # Default: routine
    
    def _route_department(self, patient: PatientProfile, diagnoses: List[Dict]) -> str:
        """Route to appropriate medical department"""
        
        # Combine text for analysis
        all_text = ' '.join(
            patient.symptoms + 
            [d['disease'] for d in diagnoses] +
            [d.get('explanation', '') for d in diagnoses]
        ).lower()
        
        # Score each department
        scores = {}
        for dept, keywords in self.DEPARTMENT_ROUTING.items():
            score = sum(1 for kw in keywords if kw in all_text)
            if score > 0:
                scores[dept] = score
        
        # Return department with highest score
        if scores:
            return max(scores, key=scores.get)
        
        return "General Medicine"
    
    def _get_triage_message(self, level: int) -> str:
        """Get action message for triage level"""
        messages = {
            1: "🚨 IMMEDIATE EMERGENCY - Call 911 or go to ER NOW",
            2: "⚠️ URGENT - Seek emergency care within 1 hour",
            3: "⚠️ PRIORITY - See a doctor within 24 hours",
            4: "ℹ️ ROUTINE - Schedule appointment within 3-7 days",
            5: "ℹ️ NON-URGENT - Routine checkup when convenient"
        }
        return messages.get(level, "")


class ReportGenerator:
    """Generate final patient report"""
    
    def generate_report(
        self, 
        patient: PatientProfile,
        diagnosis_result: Dict,
        conversation_history: List[Dict]
    ) -> str:
        """Generate comprehensive medical report"""
        
        report = []
        report.append("="*70)
        report.append("PATIENT MEDICAL ASSESSMENT REPORT")
        report.append("="*70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Patient Information
        report.append("PATIENT INFORMATION:")
        report.append("-" * 70)
        if patient.name:
            report.append(f"Name: {patient.name}")
        report.append(f"Age: {patient.age if patient.age else 'Not provided'}")
        report.append(f"Gender: {patient.gender if patient.gender else 'Not provided'}")
        report.append("")
        
        # Chief Complaints
        report.append("CHIEF COMPLAINTS:")
        report.append("-" * 70)
        for i, symptom in enumerate(patient.symptoms, 1):
            report.append(f"  {i}. {symptom.title()}")
        report.append("")
        
        # Symptom Details
        report.append("SYMPTOM DETAILS:")
        report.append("-" * 70)
        report.append(f"Duration: {patient.duration if patient.duration else 'Not specified'}")
        report.append(f"Severity: {patient.severity if patient.severity else 'Not specified'}")
        report.append("")
        
        # Medical History
        if patient.medical_history and any(patient.medical_history):
            report.append("MEDICAL HISTORY:")
            report.append("-" * 70)
            for item in patient.medical_history:
                if item and item.lower() not in ['no', 'none']:
                    report.append(f"  • {item}")
            report.append("")
        
        # Current Medications
        if patient.medications and any(patient.medications):
            report.append("CURRENT MEDICATIONS:")
            report.append("-" * 70)
            for med in patient.medications:
                if med and med.lower() not in ['no', 'none']:
                    report.append(f"  • {med}")
            report.append("")
        
        # Additional Factors
        report.append("ADDITIONAL FACTORS:")
        report.append("-" * 70)
        report.append(f"Recent Travel: {'Yes' if patient.recent_travel else 'No'}")
        report.append(f"Dietary Changes: {'Yes' if patient.dietary_changes else 'No'}")
        report.append("")
        
        # Assessment
        report.append("CLINICAL ASSESSMENT:")
        report.append("="*70)
        
        # Diagnoses with explanations
        report.append("\nDifferential Diagnoses (ranked by probability):")
        report.append("-" * 70)
        for i, diag in enumerate(diagnosis_result['diagnoses'], 1):
            prob = diag['probability'] * 100
            conf = diag['confidence']
            report.append(f"\n{i}. {diag['disease']}")
            report.append(f"   Probability: {prob:.1f}% | Confidence: {conf}")
            if 'explanation' in diag and diag['explanation']:
                report.append(f"   Clinical Note: {diag['explanation']}")
        report.append("")
        
        # Triage
        report.append("TRIAGE ASSESSMENT:")
        report.append("-" * 70)
        level = diagnosis_result['triage_level']
        report.append(f"Urgency Level: {level}/5")
        report.append(f"Recommendation: {diagnosis_result['triage_message']}")
        report.append("")
        
        # Department Recommendation
        report.append("CARE PATHWAY:")
        report.append("-" * 70)
        report.append(f"Recommended Department: {diagnosis_result['department']}")
        report.append("")
        
        # Conversation Summary
        report.append("CONSULTATION TRANSCRIPT:")
        report.append("="*70)
        for i, turn in enumerate(conversation_history, 1):
            role = turn['role'].title()
            content = turn['content']
            # Truncate very long responses
            if len(content) > 500:
                content = content[:497] + "..."
            report.append(f"\n[Turn {i}] {role}:")
            # Wrap long lines
            for line in content.split('\n'):
                if line:
                    report.append(f"    {line}")
        report.append("")
        
        # Disclaimer
        report.append("="*70)
        report.append("IMPORTANT MEDICAL DISCLAIMER:")
        report.append("-" * 70)
        report.append("This is an AI-assisted preliminary assessment and does NOT constitute")
        report.append("professional medical advice, diagnosis, or treatment. This assessment is")
        report.append("based on limited information provided in a text-based conversation and")
        report.append("should not replace an in-person evaluation by a qualified healthcare")
        report.append("professional. Please seek immediate medical attention if you are")
        report.append("experiencing a medical emergency.")
        report.append("="*70)
        
        return "\n".join(report)


class MedicalOrchestrator:
    """Main orchestrator that coordinates everything"""
    
    def __init__(self, model_name: str = "medllama2"):
        print("\n" + "="*70)
        print("INITIALIZING MEDICAL DIAGNOSTIC SYSTEM")
        print("="*70)
        
        # Initialize components
        print("\n1. Connecting to Ollama...")
        self.ollama = OllamaClient(model_name=model_name)
        
        print("2. Loading symptom extractor...")
        self.symptom_extractor = SymptomExtractor()
        
        print("3. Initializing question generator...")
        self.question_generator = QuestionGenerator(self.ollama)
        
        print("4. Loading information parser...")
        self.info_parser = InformationParser(self.symptom_extractor)
        
        print("5. Initializing diagnosis engine (MedLlama2-powered)...")
        self.diagnosis_engine = DiagnosisEngine(self.ollama)
        
        print("6. Loading report generator...")
        self.report_generator = ReportGenerator()
        
        # Initialize state
        self.reset()
        
        print("\n" + "="*70)
        print("✅ SYSTEM READY - Using MedLlama2 for diagnosis")
        print("="*70 + "\n")
    
    def reset(self):
        """Reset conversation state"""
        self.patient = PatientProfile()
        self.state = ConversationState()
        self.conversation_history = []
        self.last_response = ""
        self.current_expected_info = None
    
    def chat(self, user_input: str) -> Tuple[str, bool, Optional[str]]:
        """
        Main chat interface
        
        Returns:
            (response, is_final, report)
            - response: Bot's response to user
            - is_final: Whether this is the final diagnosis
            - report: Full report (only if is_final=True)
        """
        
        self.state.turn_count += 1
        
        # Store user message
        self.conversation_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Parse information from user's response
        if self.current_expected_info:
            extracted = self.info_parser.parse_response(
                user_input,
                self.current_expected_info,
                self.patient
            )
            if extracted:
                self.state.mark_collected(self.current_expected_info)
        
        # Always try to extract symptoms
        symptoms = self.symptom_extractor.extract(user_input)
        if symptoms:
            self.patient.symptoms.extend(symptoms)
            self.patient.symptoms = list(set(self.patient.symptoms))
            if self.patient.symptoms:
                self.state.mark_collected('primary_symptoms')
        
        # Check if ready to diagnose
        if self.state.is_complete():
            return self._finalize_diagnosis()
        
        # Generate next question
        missing = self.state.get_missing_info()
        if missing:
            self.current_expected_info = missing[0]
        
        question = self.question_generator.generate_question(
            self.state,
            self.patient,
            user_input
        )
        
        if question is None:
            # Force diagnosis
            return self._finalize_diagnosis()
        
        # Store assistant message
        self.conversation_history.append({
            'role': 'assistant',
            'content': question
        })
        
        self.last_response = user_input
        
        return question, False, None
    
    def _finalize_diagnosis(self) -> Tuple[str, bool, str]:
        """Generate final diagnosis and report"""
        
        print("\n[Generating diagnosis with MedLlama2...]")
        
        # Run diagnosis engine
        diagnosis_result = self.diagnosis_engine.diagnose(self.patient)
        
        # Generate report
        report = self.report_generator.generate_report(
            self.patient,
            diagnosis_result,
            self.conversation_history
        )
        
        # Create summary response
        response = self._create_summary_response(diagnosis_result)
        
        # Store final message
        self.conversation_history.append({
            'role': 'assistant',
            'content': response
        })
        
        return response, True, report
    
    def _create_summary_response(self, diagnosis_result: Dict) -> str:
        """Create human-readable summary"""
        
        lines = []
        lines.append("\nThank you for providing all that information. Based on our conversation, here is my medical assessment:\n")
        lines.append("="*70)
        lines.append("MEDICAL ASSESSMENT")
        lines.append("="*70 + "\n")
        
        # Symptoms
        lines.append("📋 SYMPTOMS REPORTED:")
        for symptom in self.patient.symptoms:
            lines.append(f"   • {symptom.title()}")
        lines.append("")
        
        # Diagnoses with explanations
        lines.append("🔍 DIFFERENTIAL DIAGNOSES:\n")
        for i, diag in enumerate(diagnosis_result['diagnoses'], 1):
            prob = diag['probability'] * 100
            lines.append(f"   {i}. {diag['disease']} ({prob:.1f}% probability)")
            if 'explanation' in diag and diag['explanation']:
                lines.append(f"      → {diag['explanation']}")
            lines.append("")
        
        # Department
        lines.append(f"🏥 RECOMMENDED DEPARTMENT: {diagnosis_result['department']}\n")
        
        # Triage
        level = diagnosis_result['triage_level']
        message = diagnosis_result['triage_message']
        lines.append(f"⚠️  URGENCY ASSESSMENT:")
        lines.append(f"    Level: {level}/5")
        lines.append(f"    Action: {message}\n")
        
        lines.append("="*70)
        lines.append("⚠️  CRITICAL DISCLAIMER:")
        lines.append("    This is a preliminary AI assessment and NOT a medical diagnosis.")
        lines.append("    Please consult a qualified healthcare professional for proper")
        lines.append("    medical evaluation, diagnosis, and treatment.")
        lines.append("="*70)
        
        return "\n".join(lines)
    
    def get_diagnosis_data(self) -> Dict:
        """Get structured diagnosis data for API"""
        if not self.state.is_complete():
            return None
        
        diagnosis_result = self.diagnosis_engine.diagnose(self.patient)
        return {
            'patient': self.patient.to_dict(),
            'diagnoses': diagnosis_result['diagnoses'],
            'triage_level': diagnosis_result['triage_level'],
            'department': diagnosis_result['department'],
            'triage_message': diagnosis_result['triage_message']
        }


# ============================================================================
# CLI Interface for Testing
# ============================================================================

def main():
    """Command-line interface for testing"""
    import sys
    
    print("\n" + "="*70)
    print("MEDICAL DIAGNOSTIC SYSTEM - CLI")
    print("="*70)
    print("\nCommands:")
    print("  'quit' or 'exit' - Exit the system")
    print("  'reset' - Start a new consultation")
    print("  'report' - View full report (after diagnosis)")
    print("="*70)
    
    try:
        # Initialize orchestrator (no classifier path needed)
        orchestrator = MedicalOrchestrator(model_name="medllama2")
        
    except Exception as e:
        print(f"\n❌ Error initializing system: {e}")
        print("\nMake sure:")
        print("  1. Ollama is running: ollama serve")
        print("  2. Model is available: ollama pull medllama2")
        sys.exit(1)
    
    # Start conversation
    print("\nBot: Hello! I'm here to help assess your symptoms.")
    print("     What brings you here today?\n")
    
    last_report = None
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit']:
                print("\n👋 Thank you for using the diagnostic system. Take care!")
                break
            
            if user_input.lower() == 'reset':
                orchestrator.reset()
                last_report = None
                print("\n🔄 Consultation reset.\n")
                print("Bot: Hello! What brings you here today?\n")
                continue
            
            if user_input.lower() == 'report':
                if last_report:
                    print("\n" + last_report)
                else:
                    print("\n⚠️  No report available yet. Complete the consultation first.\n")
                continue
            
            if not user_input:
                continue
            
            # Process input
            response, is_final, report = orchestrator.chat(user_input)
            
            print(f"\nBot: {response}\n")
            
            # Handle final diagnosis
            if is_final:
                last_report = report
                
                # Ask if user wants to see full report
                show_report = input("\n📄 Would you like to see the full detailed report? (yes/no): ").strip().lower()
                if show_report in ['yes', 'y']:
                    print("\n" + report)
                
                # Ask about saving report
                save_report = input("\n💾 Would you like to save this report to a file? (yes/no): ").strip().lower()
                if save_report in ['yes', 'y']:
                    filename = f"medical_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(report)
                    print(f"✅ Report saved to: {filename}")
                
                # Ask about new consultation
                another = input("\n🔄 Start another consultation? (yes/no): ").strip().lower()
                if another in ['yes', 'y']:
                    orchestrator.reset()
                    last_report = None
                    print("\nBot: Hello! What brings you here today?\n")
                else:
                    print("\n👋 Thank you for using the diagnostic system. Take care!")
                    break
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            continue


if __name__ == "__main__":
    main()