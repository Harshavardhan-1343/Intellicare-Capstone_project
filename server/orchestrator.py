import requests
import json
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

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
    is_pregnant: Optional[bool] = None
    
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
    """Ollama API client"""
    
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
        """Generate text from model"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "stop": ["\n\n", "User:", "Patient:", "Assistant:", "Doctor:", "["]
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
        # ==================== RESPIRATORY ====================
        'cough', 'shortness of breath', 'wheezing', 'chest pain', 'sore throat',
        'runny nose', 'congestion', 'sneezing', 'cold', 'stuffy nose',
        'difficulty breathing', 'tight chest', 'phlegm', 'mucus', 'chest tightness',
        'chronic cough', 'dry cough', 'wet cough', 'bloody cough', 'hemoptysis',
        'hoarseness', 'voice loss', 'laryngitis', 'stridor', 'rapid breathing',
        'shallow breathing', 'labored breathing', 'chest congestion', 'postnasal drip',
        'sinus pressure', 'nasal discharge', 'sniffles', 'nose bleed', 'epistaxis',
        
        # ==================== GASTROINTESTINAL ====================
        'nausea', 'vomiting', 'diarrhea', 'constipation', 'abdominal pain',
        'bloating', 'loss of appetite', 'heartburn', 'morning sickness', 'nauseous',
        'stomach pain', 'stomach ache', 'belly pain', 'cramping', 'gas',
        'indigestion', 'acid reflux', 'gerd', 'upset stomach', 'queasy',
        'bloody stool', 'black stool', 'tarry stool', 'rectal bleeding',
        'blood in stool', 'mucus in stool', 'pale stool', 'fatty stool',
        'foul smelling stool', 'watery diarrhea', 'chronic diarrhea',
        'abdominal cramps', 'stomach cramps', 'intestinal pain', 'bowel pain',
        'difficulty swallowing', 'dysphagia', 'feeling full', 'early satiety',
        'excessive burping', 'belching', 'flatulence', 'abdominal distension',
        'liver pain', 'jaundice', 'yellowing', 'yellow eyes', 'yellow skin',
        'loss of taste', 'metallic taste', 'bitter taste', 'food aversion',
        
        # ==================== PAIN (Specific Locations) ====================
        'headache', 'back pain', 'joint pain', 'muscle pain', 'neck pain',
        'leg pain', 'knee pain', 'ankle pain', 'shoulder pain', 'hip pain',
        'pelvic pain', 'cramping', 'cramps', 'arm pain', 'wrist pain',
        'hand pain', 'finger pain', 'toe pain', 'foot pain', 'heel pain',
        'elbow pain', 'groin pain', 'thigh pain', 'calf pain', 'shin pain',
        'lower back pain', 'upper back pain', 'middle back pain', 'tailbone pain',
        'jaw pain', 'facial pain', 'ear pain', 'eye pain', 'tooth pain',
        'throat pain', 'chest pain', 'rib pain', 'side pain', 'flank pain',
        'sciatic pain', 'sciatica', 'nerve pain', 'burning pain', 'shooting pain',
        'stabbing pain', 'throbbing pain', 'dull ache', 'sharp pain', 'chronic pain',
        'migraine', 'cluster headache', 'tension headache', 'sinus headache',
        
        # ==================== SYSTEMIC / GENERAL ====================
        'fever', 'chills', 'fatigue', 'weakness', 'sweating', 'weight loss',
        'dizziness', 'fainting', 'tired', 'exhaustion', 'dizzy', 'weak',
        'night sweats', 'cold sweats', 'hot flashes', 'flushed', 'feverish',
        'temperature', 'high temperature', 'low grade fever', 'chills and fever',
        'malaise', 'lethargy', 'sluggish', 'lack of energy', 'always tired',
        'weakness in limbs', 'general weakness', 'weight gain', 'rapid weight loss',
        'unintentional weight loss', 'appetite loss', 'increased appetite',
        'dehydration', 'excessive thirst', 'dry mouth', 'increased urination',
        'frequent urination', 'decreased urination', 'dark urine', 'bloody urine',
        'painful urination', 'burning urination', 'urgency', 'incontinence',
        'bed wetting', 'loss of consciousness', 'fainting spells', 'syncope',
        'presyncope', 'lightheaded', 'feeling faint', 'vertigo', 'spinning',
        'balance problems', 'unsteady', 'loss of balance', 'falls', 'stumbling',
        
        # ==================== NEUROLOGICAL ====================
        'confusion', 'numbness', 'tingling', 'vision changes', 'hearing loss',
        'seizures', 'tremors', 'memory loss', 'forgetfulness', 'disorientation',
        'brain fog', 'difficulty concentrating', 'loss of focus', 'mental fog',
        'blurred vision', 'double vision', 'diplopia', 'vision loss', 'blind spots',
        'floaters', 'flashing lights', 'light sensitivity', 'photophobia',
        'ringing in ears', 'tinnitus', 'ear ringing', 'muffled hearing',
        'pins and needles', 'burning sensation', 'electric shock sensation',
        'paralysis', 'weakness in limbs', 'muscle weakness', 'difficulty walking',
        'difficulty speaking', 'slurred speech', 'speech problems', 'aphasia',
        'trembling', 'shaking', 'twitching', 'muscle spasms', 'involuntary movements',
        'loss of coordination', 'clumsiness', 'difficulty with balance',
        'facial drooping', 'facial numbness', 'difficulty swallowing',
        'cognitive decline', 'memory problems', 'amnesia', 'blackouts',
        
        # ==================== CARDIOVASCULAR ====================
        'palpitations', 'irregular heartbeat', 'chest pressure', 'rapid heartbeat',
        'slow heartbeat', 'racing heart', 'fluttering', 'heart flutter',
        'skipped heartbeat', 'pounding heart', 'tachycardia', 'bradycardia',
        'chest discomfort', 'pressure in chest', 'squeezing chest', 'tight chest',
        'angina', 'heart pain', 'radiating pain', 'arm pain with chest pain',
        'cold hands', 'cold feet', 'blue fingers', 'blue toes', 'cyanosis',
        'swollen ankles', 'swollen legs', 'edema', 'leg swelling', 'foot swelling',
        'poor circulation', 'claudication', 'leg pain when walking',
        
        # ==================== DERMATOLOGICAL / SKIN ====================
        'rash', 'itching', 'swelling', 'bruising', 'pale skin',
        'hives', 'welts', 'red spots', 'skin lesions', 'bumps',
        'blisters', 'sores', 'ulcers', 'boils', 'abscess',
        'dry skin', 'flaky skin', 'peeling skin', 'cracked skin',
        'eczema', 'psoriasis', 'acne', 'pimples', 'blackheads',
        'skin discoloration', 'dark spots', 'white patches', 'vitiligo',
        'moles', 'new mole', 'changing mole', 'bleeding mole',
        'itchy skin', 'burning skin', 'skin burning', 'skin pain',
        'sensitive skin', 'red skin', 'inflamed skin', 'skin inflammation',
        'skin infection', 'pus', 'discharge from skin', 'oozing',
        'hair loss', 'alopecia', 'bald patches', 'thinning hair',
        'nail changes', 'brittle nails', 'discolored nails', 'nail pain',
        
        # ==================== GYNECOLOGICAL / PREGNANCY-RELATED ====================
        'pelvic pain', 'vaginal bleeding', 'missed period', 'cramping',
        'breast tenderness', 'tender breasts', 'spotting', 'late period', 'no period',
        'heavy bleeding', 'heavy period', 'menorrhagia', 'light period',
        'irregular period', 'painful period', 'dysmenorrhea', 'menstrual cramps',
        'abnormal discharge', 'vaginal discharge', 'foul discharge', 'bloody discharge',
        'vaginal itching', 'vaginal burning', 'vaginal pain', 'painful intercourse',
        'breast pain', 'breast lump', 'nipple discharge', 'swollen breasts',
        'morning sickness', 'pregnancy symptoms', 'breast changes',
        'ovulation pain', 'mid-cycle pain', 'pms', 'premenstrual syndrome',
        'hot flashes', 'mood swings', 'irritability', 'menopause symptoms',
        
        # ==================== URINARY ====================
        'frequent urination', 'urgent urination', 'painful urination', 'burning urination',
        'difficulty urinating', 'weak stream', 'dribbling', 'urinary retention',
        'blood in urine', 'hematuria', 'dark urine', 'cloudy urine',
        'foul smelling urine', 'urinary incontinence', 'leaking urine',
        'kidney pain', 'flank pain', 'bladder pain', 'bladder pressure',
        
        # ==================== MUSCULOSKELETAL ====================
        'stiff joints', 'joint stiffness', 'swollen joints', 'joint swelling',
        'muscle aches', 'body aches', 'sore muscles', 'muscle soreness',
        'muscle cramps', 'charlie horse', 'leg cramps', 'muscle spasms',
        'back stiffness', 'neck stiffness', 'limited range of motion',
        'difficulty moving', 'inability to bend', 'difficulty standing',
        'difficulty sitting', 'difficulty lying down', 'pain when moving',
        'arthritis pain', 'gout', 'bursitis', 'tendonitis',
        
        # ==================== PSYCHIATRIC / MENTAL HEALTH ====================
        'anxiety', 'panic', 'panic attacks', 'nervousness', 'worry',
        'depression', 'sadness', 'hopelessness', 'feeling down', 'low mood',
        'mood changes', 'irritability', 'anger', 'agitation', 'restlessness',
        'insomnia', 'sleep problems', 'difficulty sleeping', 'cant sleep',
        'excessive sleeping', 'sleeping too much', 'drowsiness', 'sleepiness',
        'nightmares', 'night terrors', 'sleep disturbances',
        'suicidal thoughts', 'thoughts of self harm', 'wanting to die',
        'hallucinations', 'hearing voices', 'seeing things', 'delusions',
        
        # ==================== ENDOCRINE / METABOLIC ====================
        'excessive hunger', 'always hungry', 'polyphagia', 'increased thirst',
        'excessive thirst', 'polydipsia', 'frequent urination', 'polyuria',
        'heat intolerance', 'cold intolerance', 'always cold', 'always hot',
        'thyroid problems', 'goiter', 'neck swelling', 'neck lump',
        
        # ==================== ALLERGIC / IMMUNOLOGIC ====================
        'allergic reaction', 'allergy symptoms', 'hay fever', 'seasonal allergies',
        'food allergy', 'drug allergy', 'anaphylaxis', 'severe allergic reaction',
        'hives', 'itchy eyes', 'watery eyes', 'red eyes', 'eye redness',
        'swollen face', 'facial swelling', 'lip swelling', 'tongue swelling',
        'difficulty breathing from allergy', 'wheezing from allergy',
        
        # ==================== INFECTIOUS / FEVER-RELATED ====================
        'infection symptoms', 'signs of infection', 'infected wound',
        'pus', 'abscess', 'swollen lymph nodes', 'swollen glands',
        'tender lymph nodes', 'lumps in neck', 'lumps under arm',
        'lumps in groin', 'body aches with fever', 'chills with fever',
        
        # ==================== EMERGENCY / SEVERE ====================
        'severe pain', 'excruciating pain', 'unbearable pain', 'worst pain ever',
        'crushing chest pain', 'sudden severe headache', 'thunderclap headache',
        'stroke symptoms', 'facial drooping', 'arm weakness', 'speech difficulty',
        'seizure', 'convulsions', 'fitting', 'loss of consciousness',
        'unresponsive', 'passed out', 'collapsed', 'heart attack symptoms',
        'cant breathe', 'choking', 'severe bleeding', 'heavy bleeding',
        'coughing up blood', 'vomiting blood', 'hematemesis',
        'severe burn', 'severe injury', 'broken bone', 'fracture',
        'head injury', 'concussion', 'unconscious', 'unresponsive',
    }
    
    def extract(self, text: str) -> List[str]:
        """Extract symptoms from text"""
        text_lower = text.lower()
        found = []
        
        # Direct matching
        for symptom in self.SYMPTOM_DATABASE:
            if symptom in text_lower:
                found.append(symptom)
                print(f"[DEBUG] Symptom found: {symptom}")
        
        # Common variations - EXPANDED
        variations = {
            # Respiratory
            'can\'t breathe': 'difficulty breathing',
            'cannot breathe': 'difficulty breathing',
            'hard to breathe': 'difficulty breathing',
            'trouble breathing': 'difficulty breathing',
            'out of breath': 'shortness of breath',
            'winded': 'shortness of breath',
            'stuffy': 'congestion',
            'blocked nose': 'congestion',
            'nose blocked': 'congestion',
            
            # GI
            'stomach pain': 'abdominal pain',
            'stomach ache': 'abdominal pain',
            'belly ache': 'abdominal pain',
            'tummy ache': 'abdominal pain',
            'throwing up': 'vomiting',
            'throw up': 'vomiting',
            'puking': 'vomiting',
            'upset stomach': 'nausea',
            'feel sick': 'nausea',
            'feeling sick': 'nausea',
            'queasy': 'nausea',
            'sick to stomach': 'nausea',
            'loose stool': 'diarrhea',
            'runny stool': 'diarrhea',
            'runs': 'diarrhea',
            'the runs': 'diarrhea',
            
            # Temperature
            'temperature': 'fever',
            'hot': 'fever',
            'feverish': 'fever',
            'burning up': 'fever',
            'high temp': 'fever',
            
            # Energy
            'tired': 'fatigue',
            'exhausted': 'fatigue',
            'worn out': 'fatigue',
            'drained': 'fatigue',
            'no energy': 'fatigue',
            'wiped out': 'fatigue',
            
            # Dizziness
            'dizzy': 'dizziness',
            'lightheaded': 'dizziness',
            'light headed': 'dizziness',
            'head spinning': 'dizziness',
            'room spinning': 'vertigo',
            
            # Pain
            'sore': 'pain',
            'aching': 'pain',
            'hurts': 'pain',
            'painful': 'pain',
            
            # Pregnancy/Period
            'late period': 'missed period',
            'no period': 'missed period',
            'period late': 'missed period',
            'haven\'t had period': 'missed period',
            'skipped period': 'missed period',
            'sore breasts': 'breast tenderness',
            'tender breasts': 'breast tenderness',
            'painful breasts': 'breast tenderness',
            
            # Mental
            'can\'t sleep': 'insomnia',
            'cannot sleep': 'insomnia',
            'trouble sleeping': 'insomnia',
            'anxious': 'anxiety',
            'nervous': 'anxiety',
            'worried': 'anxiety',
            'depressed': 'depression',
            'sad': 'depression',
            
            # Skin
            'bumps': 'rash',
            'spots': 'rash',
            'blemishes': 'rash',
            'itchy': 'itching',
            'scratchy': 'itching',
            
            # Movement
            'difficulty walking': 'leg pain',
            'hard to walk': 'leg pain',
            'trouble walking': 'leg pain',
            'can\'t walk': 'leg pain',
            'difficulty moving': 'joint pain',
            
            # Vision/Hearing
            'blurry vision': 'blurred vision',
            'fuzzy vision': 'blurred vision',
            'can\'t see clearly': 'blurred vision',
            'ringing ears': 'tinnitus',
            'ears ringing': 'tinnitus',
            'buzzing in ears': 'tinnitus',
            
            # Urinary
            'burning when peeing': 'burning urination',
            'painful urination': 'burning urination',
            'hurts to pee': 'burning urination',
            'frequent peeing': 'frequent urination',
            'peeing a lot': 'frequent urination',
        }
        
        for variant, canonical in variations.items():
            if variant in text_lower and canonical not in found:
                found.append(canonical)
                print(f"[DEBUG] Symptom found via variation '{variant}': {canonical}")
        
        if found:
            print(f"[DEBUG] Total symptoms extracted: {found}")
        else:
            print(f"[DEBUG] No symptoms found in: '{text_lower}'")
        
        return list(set(found))


class ConversationState:
    """Tracks conversation state and what information is needed"""
    
    REQUIRED_INFO = [
        'age',
        'gender',
        'primary_symptoms',
        'symptom_duration',
        'symptom_severity',
        'medical_history',
    ]
    
    CRITICAL_INFO = [
        'primary_symptoms',
        'symptom_duration',
        'symptom_severity',
        'medical_history',
    ]
    
    OPTIONAL_INFO = [
        'age',
        'gender',
    ]
    
    def __init__(self):
        self.collected = set()
        self.skipped = set()
        self.turn_count = 0
        self.symptom_specific_questions_asked = 0
        self.max_symptom_questions = 3
        self.max_turns = 15
        self.pregnancy_question_asked = False
        self.question_attempt_count = {}
        self.last_question_asked = None
        self.symptom_question_attempts = 0
        self.is_first_user_message = True
    
    def mark_collected(self, info_type: str):
        """Mark information as collected"""
        self.collected.add(info_type)
        print(f"[DEBUG] Marked as collected: {info_type}. Total collected: {self.collected}")
    
    def mark_skipped(self, info_type: str):
        """Mark information as skipped by user"""
        if info_type in self.OPTIONAL_INFO:
            self.skipped.add(info_type)
            print(f"[DEBUG] User chose to skip: {info_type}")
        else:
            print(f"[DEBUG] Cannot skip {info_type} - it's required")
    
    def increment_attempt(self, info_type: str) -> int:
        """Increment and return attempt count for a question"""
        if info_type not in self.question_attempt_count:
            self.question_attempt_count[info_type] = 0
        self.question_attempt_count[info_type] += 1
        return self.question_attempt_count[info_type]
    
    def mark_symptom_question_asked(self):
        """Mark that a symptom-specific question was asked and answered"""
        self.symptom_specific_questions_asked += 1
        self.symptom_question_attempts = 0  # Reset attempts for next question
        print(f"[DEBUG] Completed symptom question {self.symptom_specific_questions_asked}/3")
    
    def is_complete(self) -> bool:
        """Check if we have enough information"""
        critical_collected = all(
            info in self.collected for info in self.CRITICAL_INFO
        )
        
        optional_handled = all(
            info in self.collected or info in self.skipped 
            for info in self.OPTIONAL_INFO
        )
        
        enough_symptom_questions = self.symptom_specific_questions_asked >= self.max_symptom_questions
        
        return (
            critical_collected and optional_handled and enough_symptom_questions
        ) or (
            self.turn_count >= self.max_turns and critical_collected
        )
    
    def get_missing_info(self) -> List[str]:
        """Get list of missing required information"""
        return [
            info for info in self.REQUIRED_INFO 
            if info not in self.collected and info not in self.skipped
        ]
    
    def can_ask_symptom_question(self) -> bool:
        """Check if we can ask more symptom-specific questions"""
        return self.symptom_specific_questions_asked < self.max_symptom_questions


class QuestionGenerator:
    """Generate appropriate questions based on conversation state"""
    
    PREGNANCY_RELEVANT_SYMPTOMS = [
        'nausea', 'vomiting', 'fatigue', 'missed period', 'abdominal pain',
        'pelvic pain', 'cramping', 'vaginal bleeding', 'dizziness', 'weakness',
        'morning sickness', 'tender breasts', 'breast tenderness'
    ]
    
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
            return "Hello! I'm your medical assistant. Describe your symptoms and I'll help assess and triage your condition."
        
        missing = state.get_missing_info()
        print(f"[DEBUG] Missing info: {missing}")
        print(f"[DEBUG] Skipped info: {state.skipped}")
        print(f"[DEBUG] Collected info: {state.collected}")
        print(f"[DEBUG] Current patient data - Age: {patient.age}, Gender: {patient.gender}, Duration: {patient.duration}, Severity: {patient.severity}, Medical History: {patient.medical_history}")
        
        # Phase 1: Collect REQUIRED information (ONE at a time, in order)
        if missing:
            # Priority 1: Ask for age (OPTIONAL)
            if 'age' in missing:
                return "May I ask your age? (You can say 'skip' if you prefer not to share)"
            
            # Priority 2: Ask for gender (OPTIONAL)
            if 'gender' in missing:
                return "What is your gender? (You can say 'skip' if you prefer not to share)"
            
            # Priority 3: Ask for duration (REQUIRED)
            if 'symptom_duration' in missing:
                return "How long have you been experiencing these symptoms?"
            
            # Priority 4: Ask for severity (REQUIRED)
            if 'symptom_severity' in missing:
                return "On a scale of 1-10, how severe would you rate your symptoms?"
            
            # Priority 5: Ask for medical history (REQUIRED)
            if 'medical_history' in missing:
                print("[DEBUG] Asking mandatory medical history question")
                return "Do you have any medical history or chronic conditions (like diabetes, hypertension, asthma, heart disease, etc.) that I should know about?"
        
        # PREGNANCY CHECK
        if not missing:
            is_female = patient.gender and patient.gender.lower() in ['female', 'woman', 'f']
            is_childbearing_age = patient.age and 15 <= patient.age <= 50
            has_relevant_symptoms = self._is_pregnancy_relevant(patient.symptoms)
            
            print(f"[DEBUG] Pregnancy check:")
            print(f"  - Is female: {is_female} (gender: {patient.gender})")
            print(f"  - Childbearing age: {is_childbearing_age} (age: {patient.age})")
            print(f"  - Has relevant symptoms: {has_relevant_symptoms} (symptoms: {patient.symptoms})")
            print(f"  - Already asked: {state.pregnancy_question_asked}")
            
            if (not state.pregnancy_question_asked and 
                is_female and
                has_relevant_symptoms):
                
                if patient.age is None:
                    print("[DEBUG] Age unknown but asking pregnancy question due to relevant symptoms")
                
                state.pregnancy_question_asked = True
                print("[DEBUG] Asking pregnancy question")
                return "Is there any chance you could be pregnant, or are you currently pregnant? (You can say 'skip' if you prefer not to share)"
            elif not state.pregnancy_question_asked:
                print(f"[DEBUG] Skipping pregnancy question - Female: {is_female}, Age OK: {is_childbearing_age}, Symptoms relevant: {has_relevant_symptoms}")
        
        # Phase 2: Symptom-specific questions
        if not missing and state.can_ask_symptom_question() and patient.symptoms:
            if state.symptom_question_attempts >= 2:
                print(f"[DEBUG] Moving on from current symptom question after 2 attempts")
                state.mark_symptom_question_asked()
            
            if state.can_ask_symptom_question():
                state.symptom_question_attempts += 1
                print(f"[DEBUG] Generating symptom question {state.symptom_specific_questions_asked + 1}/3 (attempt {state.symptom_question_attempts})")
                
                question = self._generate_symptom_specific_question(patient, last_response, state)
                
                if question == state.last_question_asked:
                    print(f"[DEBUG] Generated duplicate question, using fallback")
                    question = self._get_fallback_symptom_question(patient, state)
                
                state.last_question_asked = question
                return question
        
        # Ready to diagnose
        print("[DEBUG] All information collected, ready to diagnose")
        return None
    
    def _is_pregnancy_relevant(self, symptoms: List[str]) -> bool:
        """Check if pregnancy question is relevant based on symptoms"""
        if not symptoms:
            print("[DEBUG] No symptoms to check")
            return False
        
        symptom_str = ' '.join(symptoms).lower()
        print(f"[DEBUG] Checking pregnancy relevance for: {symptom_str}")
        
        for preg_symptom in self.PREGNANCY_RELEVANT_SYMPTOMS:
            if preg_symptom in symptom_str:
                print(f"[DEBUG] Found pregnancy-relevant symptom: {preg_symptom}")
                return True
        
        print("[DEBUG] No pregnancy-relevant symptoms found")
        return False
    
    def _generate_symptom_specific_question(
        self, 
        patient: PatientProfile,
        last_response: str,
        state: ConversationState
    ) -> str:
        """Generate intelligent symptom-specific follow-up questions using LLM"""
        
        symptoms_str = ", ".join(patient.symptoms)
        duration_str = patient.duration if patient.duration else "unknown duration"
        severity_str = patient.severity if patient.severity else "unknown severity"
        medical_history_str = ", ".join(patient.medical_history) if patient.medical_history else "none reported"
        
        # Build context of what we already know
        known_info = f"""Patient already told us:
- Symptoms: {symptoms_str}
- Duration: {duration_str}
- Severity: {severity_str}
- Medical history: {medical_history_str}
- Previous answer: "{last_response}"
"""
        
        prompt = f"""You are a medical assistant asking follow-up questions about symptoms.

{known_info}

This is question {state.symptom_specific_questions_asked + 1} of 3.

Generate ONE brief follow-up question to gather NEW information we don't already have.

DO NOT ask about:
- Duration (we already know: {duration_str})
- Severity (we already know: {severity_str})
- Medical history (we already know: {medical_history_str})

Focus areas for this question:
Question 1: Associated symptoms they haven't mentioned (fever, nausea, headache, etc.)
Question 2: Timing and triggers (worse at certain times? triggered by activity?)
Question 3: Impact and relief (what helps? how does it affect daily life?)

Rules:
- Keep under 20 words
- Include examples in parentheses when helpful
- Ask ONLY one question
- Don't repeat what they already told us

Question:"""
        
        question = self.ollama.generate(prompt, max_tokens=60, temperature=0.7)
        question = self._clean_llm_response(question)
        
        # Validate question doesn't ask about duration/severity again
        question_lower = question.lower()
        if any(phrase in question_lower for phrase in ['how long', 'duration', 'how severe', 'rate', 'scale of']):
            print("[DEBUG] Generated question asks about info we already have, using fallback")
            return self._get_fallback_symptom_question(patient, state)
        
        if len(question) < 10 or len(question) > 250:
            return self._get_fallback_symptom_question(patient, state)
        
        return question
    
    def _clean_llm_response(self, response: str) -> str:
        """Clean LLM response while keeping helpful clarifying options in parentheses"""
        
        response = re.sub(r'^(Question:|Here\'s a question:|I would ask:|Ask:|Query:)', '', response, flags=re.IGNORECASE).strip()
        response = re.sub(r'\[.*?\]', '', response)
        
        instruction_patterns = [
            r'\(.*?taking notes.*?\)',
            r'\(.*?preparing.*?\)',
            r'\(.*?assessment.*?\)',
            r'\(.*?while.*?\)',
            r'\(.*?next step.*?\)',
            r'\(.*?these questions.*?\)',
        ]
        
        for pattern in instruction_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        sentences = response.split('.')
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and not any(phrase in sentence.lower() for phrase in [
                'taking notes', 'preparing for', 'next step in',
                'these questions', 'ask these', 'mr.', 'mrs.', 'ms.',
                'during the assessment', 'while examining'
            ]):
                cleaned_sentences.append(sentence)
        
        response = '. '.join(cleaned_sentences).strip()
        
        if '?' in response:
            first_question = response.split('?')[0] + '?'
            response = first_question
        
        response = response.rstrip('.,;:!')
        
        if not response.endswith('?'):
            response = response + '?'
        
        return response.strip()
    
    def _get_fallback_symptom_question(self, patient: PatientProfile, state: ConversationState) -> str:
        """Fallback symptom-specific questions if LLM generation fails"""
        
        symptom_str = ' '.join(patient.symptoms).lower()
        current_question_num = state.symptom_specific_questions_asked + 1
        
        print(f"[DEBUG] Using fallback question #{current_question_num} for symptoms: {symptom_str}")
        
        # Question 1: Associated symptoms
        if current_question_num == 1:
            if any(s in symptom_str for s in ['dizzy', 'dizziness', 'weak', 'weakness']):
                return "Are you experiencing any other symptoms like nausea, headache, blurred vision, or chest pain?"
            elif 'fever' in symptom_str:
                return "Do you have any other symptoms like cough, body aches, headache, or sore throat?"
            elif 'pain' in symptom_str:
                return "Can you describe the pain quality (sharp, dull, throbbing, or burning)?"
            else:
                return "Are there any other symptoms you've noticed along with this?"
        
        # Question 2: Timing and triggers
        elif current_question_num == 2:
            if any(s in symptom_str for s in ['dizzy', 'dizziness']):
                return "Does the dizziness happen all the time, or is it triggered by certain movements (like standing up or turning your head)?"
            elif any(s in symptom_str for s in ['weak', 'weakness']):
                return "Is the weakness constant throughout the day, or does it get worse at certain times?"
            elif 'pain' in symptom_str:
                return "When does the pain feel the worst (morning, evening, during activity, at rest)?"
            else:
                return "Are your symptoms constant or do they come and go?"
        
        # Question 3: Relief and impact
        else:
            if any(s in symptom_str for s in ['dizzy', 'dizziness', 'weak', 'weakness']):
                return "Have you noticed anything that makes you feel better (like rest, eating, drinking fluids)?"
            elif 'pain' in symptom_str:
                return "What helps relieve the pain (rest, medications, heat/ice)?"
            else:
                return "How are these symptoms affecting your daily activities?"


class InformationParser:
    """Parse patient responses to extract structured information"""
    
    def __init__(self, symptom_extractor: SymptomExtractor):
        self.symptom_extractor = symptom_extractor
    
    def parse_response(
        self, 
        text: str, 
        patient: PatientProfile,
        state: ConversationState
    ) -> None:
        """Parse response and update patient profile"""
        
        text_lower = text.lower().strip()
        
        # Check for skip/decline responses
        skip_phrases = ['skip', 'prefer not to say', 'prefer not to share', 'rather not say', 
                       'dont want to', "don't want to", 'pass', 'next question']
        is_skip_response = any(phrase in text_lower for phrase in skip_phrases)
        
        # Check for "no" as a decline to OPTIONAL questions only (but ONLY for specific questions)
        is_declining_optional = text_lower in ['no', 'nope', 'nah'] and len(text_lower.split()) <= 2
        
        # Always extract symptoms first
        symptoms = self.symptom_extractor.extract(text)
        print(f"[DEBUG] Extracted symptoms from '{text[:50]}...': {symptoms}")
        
        if symptoms:
            new_symptoms = [s for s in symptoms if s not in patient.symptoms]
            if new_symptoms:
                print(f"[DEBUG] Adding new symptoms: {new_symptoms}")
            patient.symptoms.extend(new_symptoms)
            patient.symptoms = list(set(patient.symptoms))
            if patient.symptoms:
                state.mark_collected('primary_symptoms')
                print(f"[DEBUG] Total patient symptoms now: {patient.symptoms}")
        else:
            print(f"[DEBUG] No symptoms extracted from this response")
        
        # Determine which question we're currently expecting an answer for
        missing = state.get_missing_info()
        current_question = missing[0] if missing else None
        print(f"[DEBUG] Current expected question: {current_question}")
        
        # Extract age (OPTIONAL - can skip)
        if 'age' not in state.collected and 'age' not in state.skipped:
            if current_question == 'age':  # ONLY process if we're asking for age
                if is_skip_response or (is_declining_optional and 'age' in missing):
                    state.mark_skipped('age')
                    print("[DEBUG] User explicitly declined to provide age")
                    return  # IMPORTANT: Return immediately, don't process other fields
                else:
                    age = self._extract_age(text)
                    if age:
                        patient.age = age
                        state.mark_collected('age')
                        return  # IMPORTANT: Return after collecting
        
        # Extract gender (OPTIONAL - can skip)
        if 'gender' not in state.collected and 'gender' not in state.skipped:
            if current_question == 'gender':  # ONLY process if we're asking for gender
                if is_skip_response or (is_declining_optional and 'gender' in missing):
                    state.mark_skipped('gender')
                    print("[DEBUG] User explicitly declined to provide gender")
                    return  # IMPORTANT: Return immediately
                else:
                    gender = self._extract_gender(text)
                    if gender:
                        patient.gender = gender
                        state.mark_collected('gender')
                        print(f"[DEBUG] Gender extracted and stored: {gender}")
                        return  # IMPORTANT: Return after collecting
        
        # Extract duration (REQUIRED - cannot be skipped)
        if not patient.duration:
            if current_question == 'symptom_duration':
                duration = self._extract_duration(text)
                if duration:
                    patient.duration = duration
                    state.mark_collected('symptom_duration')
                    print(f"[DEBUG] Duration extracted and marked: {duration}")
                    return
        
        # Extract severity (REQUIRED - cannot be skipped)
        if not patient.severity and 'symptom_severity' not in state.collected:
            if current_question == 'symptom_severity':
                if any(word in text_lower for word in ['rate', 'scale', 'severe', 'mild', 'moderate', 'pain level']) or re.match(r'^\s*\d+\s*$', text):
                    severity = self._extract_severity(text)
                    if severity:
                        patient.severity = severity
                        state.mark_collected('symptom_severity')
                        return
        
        # Extract medical history (REQUIRED - CANNOT be skipped)
        if 'medical_history' not in state.collected:
            basic_info_collected = (
                'symptom_duration' in state.collected and 
                'symptom_severity' in state.collected
            )
            
            if basic_info_collected and current_question == 'medical_history':
                is_medical_history_response = self._is_medical_history_question_response(text_lower)
                
                if is_medical_history_response:
                    medical_history_info = self._extract_medical_history(text)
                    if medical_history_info is not None:
                        if medical_history_info:
                            patient.medical_history.extend(medical_history_info)
                            patient.medical_history = list(set(patient.medical_history))
                        state.mark_collected('medical_history')
                        print(f"[DEBUG] Medical history collected: {patient.medical_history if patient.medical_history else 'None reported'}")
                        return
                else:
                    print("[DEBUG] Not a medical history response yet, waiting for proper answer")
        
        # Extract pregnancy status (can be skipped)
        if patient.gender and patient.gender.lower() in ['female', 'woman', 'f']:
            if patient.is_pregnant is None:
                if is_skip_response:
                    patient.is_pregnant = False
                    print("[DEBUG] User skipped pregnancy question")
                else:
                    pregnancy = self._extract_pregnancy_status(text)
                    if pregnancy is not None:
                        patient.is_pregnant = pregnancy
    
    def _extract_age(self, text: str) -> Optional[int]:
        """Extract age from text"""
        numbers = re.findall(r'\b(\d{1,3})\b', text)
        for num in numbers:
            age = int(num)
            if 0 < age < 120:
                return age
        return None
    
    def _extract_gender(self, text: str) -> Optional[str]:
        """Extract gender from text - FIXED"""
        text_lower = text.lower().strip()
        
        # Check female FIRST to avoid false positives
        if any(word in text_lower for word in ['female', 'woman', 'girl', 'lady']):
            return 'female'
        elif any(word in text_lower for word in ['male', 'man', 'boy', 'gentleman']):
            # IMPORTANT: Make sure 'female' is not in the text
            if 'female' not in text_lower:
                return 'male'
        
        # Check for single letter or word responses
        if text_lower == 'f' or text_lower == 'female':
            return 'female'
        elif text_lower == 'm' or text_lower == 'male':
            return 'male'
        
        return None
    
    def _is_medical_history_question_response(self, text_lower: str) -> bool:
        """Check if the response is answering the medical history question"""
        # If the response is very short
        if len(text_lower.split()) <= 5:
            return True
        
        # If it contains medical condition keywords
        medical_keywords = ['diabetes', 'hypertension', 'asthma', 'heart', 'kidney', 
                          'liver', 'thyroid', 'cancer', 'arthritis', 'epilepsy', 
                          'stroke', 'copd', 'migraine', 'depression', 'allergy']
        if any(keyword in text_lower for keyword in medical_keywords):
            return True
        
        # If it's a clear negative response
        if any(neg in text_lower for neg in ['no', 'none', 'nothing', 'nope', 'not that i know']):
            return True
        
        return False
    
    def _extract_medical_history(self, text: str) -> Optional[List[str]]:
        """Extract medical history from text"""
        text_lower = text.lower().strip()
        
        # Check for negative responses
        if text_lower in ['no', 'none', 'nope', 'nothing', 'not really', 'no medical history']:
            print("[DEBUG] Medical history: Negative response detected")
            return []
        
        negative_phrases = ['no medical', 'no chronic', 'nothing', 'not that i know', 
                           'no history', 'no conditions', "don't have any"]
        if any(phrase in text_lower for phrase in negative_phrases) and len(text_lower.split()) <= 10:
            print("[DEBUG] Medical history: Negative phrase detected")
            return []
        
        # Common medical conditions
        medical_conditions = {
            'diabetes': ['diabetes', 'diabetic', 'sugar'],
            'hypertension': ['hypertension', 'high blood pressure', 'bp'],
            'asthma': ['asthma', 'breathing problem'],
            'heart disease': ['heart disease', 'cardiac', 'heart problem', 'heart attack', 'angina'],
            'kidney disease': ['kidney', 'renal'],
            'liver disease': ['liver', 'hepatitis'],
            'thyroid': ['thyroid', 'hyperthyroid', 'hypothyroid'],
            'cancer': ['cancer', 'tumor', 'malignancy'],
            'arthritis': ['arthritis', 'joint disease'],
            'epilepsy': ['epilepsy', 'seizures', 'fits'],
            'stroke': ['stroke', 'cva'],
            'copd': ['copd', 'emphysema', 'chronic bronchitis'],
            'migraine': ['migraine', 'chronic headache'],
            'depression': ['depression', 'anxiety', 'mental health'],
            'allergies': ['allergy', 'allergies', 'allergic'],
        }
        
        found_conditions = []
        for condition, keywords in medical_conditions.items():
            if any(keyword in text_lower for keyword in keywords):
                found_conditions.append(condition)
        
        if found_conditions:
            print(f"[DEBUG] Medical history: Found conditions: {found_conditions}")
            return found_conditions
        
        # If text contains medical-sounding info but no specific match
        if len(text.strip()) > 10 and not any(neg in text_lower for neg in ['no', 'none', 'nothing']):
            print(f"[DEBUG] Medical history: Storing raw text: {text.strip()}")
            return [text.strip()]
        
        return None
    
    def _extract_duration(self, text: str) -> Optional[str]:
        """Extract duration from text"""
        text_lower = text.lower()
        
        patterns = [
            (r'(\d+)\s*days?', 'days'),
            (r'(\d+)\s*weeks?', 'weeks'),
            (r'(\d+)\s*months?', 'months'),
            (r'(\d+)\s*years?', 'years'),
            (r'(\d+)\s*hours?', 'hours'),
        ]
        
        for pattern, unit in patterns:
            match = re.search(pattern, text_lower)
            if match:
                number = match.group(1)
                print(f"[DEBUG] Found duration pattern: {number} {unit}")
                return f"{number} {unit}"
        
        if 'yesterday' in text_lower or 'since yesterday' in text_lower:
            return '1 day'
        if 'today' in text_lower or 'this morning' in text_lower:
            return 'less than 1 day'
        if 'last week' in text_lower:
            return '1 week'
        if 'last month' in text_lower:
            return '1 month'
        
        text_numbers = {
            'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
            'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
            'couple': '2', 'few': '3', 'several': '3'
        }
        
        for word, num in text_numbers.items():
            if f'{word} day' in text_lower:
                return f'{num} days'
            if f'{word} week' in text_lower:
                return f'{num} weeks'
            if f'{word} month' in text_lower:
                return f'{num} months'
            if f'{word} year' in text_lower:
                return f'{num} years'
        
        return None
    
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
        if any(word in text_lower for word in ['severe', 'extreme', 'unbearable', 'worst', 'terrible', 'intense']):
            return 'severe'
        if any(word in text_lower for word in ['moderate', 'manageable', 'noticeable', 'significant', 'fairly bad']):
            return 'moderate'
        if any(word in text_lower for word in ['mild', 'slight', 'minor', 'little', 'light', 'bearable']):
            return 'mild'
        
        return None
    
    def _extract_pregnancy_status(self, text: str) -> Optional[bool]:
        """Extract pregnancy status from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['yes', 'pregnant', 'expecting', 'i am']):
            return True
        elif any(word in text_lower for word in ['no', 'not pregnant', "i'm not", "not"]):
            return False
        
        return None


# [DiagnosisEngine with FIXED triage logic]

class DiagnosisEngine:
    """Generate diagnosis"""
    
    TRIAGE_CRITERIA = {
        1: {  # IMMEDIATE EMERGENCY
            'keywords': ['chest pain', 'difficulty breathing', 'severe bleeding', 
                        'loss of consciousness', 'stroke', 'heart attack', 'severe trauma',
                        'unconscious', 'not breathing', 'severe burn'],
            'severity_min': 9
        },
        2: {  # URGENT
            'keywords': ['severe pain', 'high fever', 'confusion', 'significant bleeding',
                        'suspected fracture', 'severe allergic reaction', 'dehydration'],
            'severity_min': 8
        },
        3: {  # PRIORITY
            'keywords': ['persistent fever', 'significant pain', 'infection signs',
                        'persistent vomiting'],
            'severity_min': 6
        },
        4: {  # ROUTINE
            'keywords': ['moderate pain', 'persistent symptoms', 'minor infection', 'fever'],
            'severity_min': 4
        },
        5: {  # NON-URGENT
            'keywords': ['mild symptoms', 'chronic condition management', 'mild pain'],
            'severity_min': 0
        }
    }
    
    DEPARTMENT_ROUTING = {
        'Emergency Medicine': ['severe', 'acute', 'trauma', 'immediate', 'emergency', 'life-threatening'],
        'Cardiology': ['chest pain', 'heart', 'palpitation', 'cardiac', 'angina', 'hypertension'],
        'Pulmonology': ['breathing', 'cough', 'lung', 'respiratory', 'asthma', 'pneumonia'],
        'Gastroenterology': ['abdominal pain', 'nausea', 'vomiting', 'diarrhea', 'stomach', 'liver'],
        'Neurology': ['headache', 'migraine', 'numbness', 'seizure', 'stroke', 'confusion', 'dizziness'],
        'Orthopedics': ['bone', 'joint pain', 'fracture', 'sprain', 'back pain', 'arthritis', 'leg pain', 'knee pain', 'ankle pain'],
        'Dermatology': ['rash', 'itching', 'skin', 'swelling', 'lesion'],
        'ENT': ['sore throat', 'ear pain', 'hearing', 'runny nose', 'sinus'],
        'Infectious Disease': ['fever', 'infection', 'sepsis', 'tuberculosis', 'influenza'],
        'Obstetrics & Gynecology': ['pregnant', 'pregnancy', 'pelvic pain', 'vaginal bleeding', 'missed period'],
        'General Medicine': []
    }
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
        print("✓ Diagnosis engine initialized")
    
    def diagnose(self, patient: PatientProfile) -> Dict:
        print("\n[Analyzing patient data...]")
        diagnoses = self._get_llm_diagnosis(patient)
        triage_level = self._calculate_triage(patient, diagnoses)
        department = self._route_department(patient, diagnoses)
        triage_message = self._get_triage_message(triage_level)
        
        return {
            'diagnoses': diagnoses,
            'triage_level': triage_level,
            'triage_message': triage_message,
            'department': department,
            'patient_profile': patient.to_dict()
        }
    
    def _get_llm_diagnosis(self, patient: PatientProfile) -> List[Dict]:
        prompt = self._create_diagnosis_prompt(patient)
        response = self.ollama.generate(prompt, max_tokens=500, temperature=0.3)
        diagnoses = self._parse_diagnosis_response(response)
        
        if not diagnoses or len(diagnoses) == 0:
            diagnoses = self._fallback_diagnosis(patient)
        
        return diagnoses[:3]
    
    def _create_diagnosis_prompt(self, patient: PatientProfile) -> str:
        prompt = """You are an experienced medical doctor. Based on the patient information below, provide the top 3 most likely differential diagnoses.

PATIENT INFORMATION:
"""
        if patient.age:
            prompt += f"Age: {patient.age} years\n"
        if patient.gender:
            prompt += f"Gender: {patient.gender}\n"
        if patient.is_pregnant is not None:
            prompt += f"Pregnant: {'Yes' if patient.is_pregnant else 'No'}\n"
        
        if patient.symptoms:
            prompt += f"\nChief Complaints:\n"
            for symptom in patient.symptoms:
                prompt += f"  - {symptom}\n"
        
        if patient.duration:
            prompt += f"\nDuration: {patient.duration}\n"
        
        if patient.severity:
            prompt += f"Severity: {patient.severity}\n"
        
        if patient.medical_history and any(patient.medical_history):
            prompt += f"\nMedical History:\n"
            for item in patient.medical_history:
                if item and item.lower() not in ['no', 'none', 'nothing']:
                    prompt += f"  - {item}\n"
        
        prompt += """
TASK: Provide exactly 3 differential diagnoses in this exact format:

1. [Disease Name] - [Probability percentage]% - Brief explanation (1-2 sentences)
2. [Disease Name] - [Probability percentage]% - Brief explanation (1-2 sentences)
3. [Disease Name] - [Probability percentage]% - Brief explanation (1-2 sentences)

Guidelines:
- List from most likely to least likely
- Probability should be realistic and match the clinical picture
- For acute symptoms of short duration (days), prioritize common acute conditions
- For fever of 2-3 days with mild severity, think viral infection, flu, common cold
- Do NOT suggest rare diseases like tuberculosis for simple short-duration fever
- Consider age, gender, symptoms, duration, and severity
- Keep explanations brief and clinical

Your diagnosis:"""
        
        return prompt
    
    def _parse_diagnosis_response(self, response: str) -> List[Dict]:
        diagnoses = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.\s', line):
                try:
                    line = re.sub(r'^\d+\.\s*', '', line)
                    parts = line.split('-')
                    
                    if len(parts) >= 2:
                        disease_name = parts[0].strip()
                        prob_match = re.search(r'(\d+(?:\.\d+)?)\s*%', parts[1])
                        if prob_match:
                            probability = float(prob_match.group(1)) / 100
                        else:
                            probability = 0.7 / (len(diagnoses) + 1)
                        
                        explanation = '-'.join(parts[2:]).strip() if len(parts) > 2 else parts[1].strip()
                        explanation = re.sub(r'\d+(?:\.\d+)?%', '', explanation).strip()
                        
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
                            'explanation': explanation[:200]
                        })
                except Exception as e:
                    print(f"Warning: Could not parse diagnosis line: {line} - {e}")
                    continue
        
        return diagnoses
    
    def _fallback_diagnosis(self, patient: PatientProfile) -> List[Dict]:
        """Improved fallback with realistic diagnoses based on symptoms and duration"""
        symptom_str = ' '.join(patient.symptoms).lower()
        duration_str = (patient.duration or '').lower()
        diagnoses = []
        
        # Check duration - short duration = acute conditions
        is_short_duration = any(term in duration_str for term in ['day', 'days', 'hour', 'hours', 'yesterday', 'today'])
        
        # Fever-related diagnoses
        if 'fever' in symptom_str:
            if is_short_duration:
                diagnoses = [
                    {
                        'disease': 'Viral Upper Respiratory Infection',
                        'probability': 0.65,
                        'confidence': 'moderate',
                        'explanation': 'Common viral infection causing fever and systemic symptoms'
                    },
                    {
                        'disease': 'Influenza',
                        'probability': 0.25,
                        'confidence': 'moderate',
                        'explanation': 'Flu virus causing acute fever and body aches'
                    },
                    {
                        'disease': 'Viral Syndrome',
                        'probability': 0.10,
                        'confidence': 'low',
                        'explanation': 'Non-specific viral illness'
                    }
                ]
            else:
                diagnoses = [
                    {
                        'disease': 'Bacterial Infection',
                        'probability': 0.50,
                        'confidence': 'moderate',
                        'explanation': 'Persistent fever may indicate bacterial infection requiring evaluation'
                    },
                    {
                        'disease': 'Chronic Viral Infection',
                        'probability': 0.30,
                        'confidence': 'low',
                        'explanation': 'Prolonged viral illness'
                    },
                    {
                        'disease': 'Other Infectious Disease',
                        'probability': 0.20,
                        'confidence': 'low',
                        'explanation': 'Requires further diagnostic workup'
                    }
                ]
        
        # Leg pain-related
        elif any(s in symptom_str for s in ['leg pain', 'knee pain']):
            diagnoses = [
                {
                    'disease': 'Musculoskeletal Strain',
                    'probability': 0.60,
                    'confidence': 'moderate',
                    'explanation': 'Muscle or joint strain from overuse or injury'
                },
                {
                    'disease': 'Osteoarthritis',
                    'probability': 0.30,
                    'confidence': 'low',
                    'explanation': 'Degenerative joint disease'
                },
                {
                    'disease': 'Peripheral Neuropathy',
                    'probability': 0.10,
                    'confidence': 'low',
                    'explanation': 'Nerve-related pain'
                }
            ]
        
        # Default
        else:
            diagnoses = [
                {
                    'disease': 'Non-specific Illness',
                    'probability': 0.60,
                    'confidence': 'low',
                    'explanation': 'Symptoms require in-person medical evaluation for accurate diagnosis'
                },
                {
                    'disease': 'Viral Syndrome',
                    'probability': 0.30,
                    'confidence': 'low',
                    'explanation': 'General viral illness'
                },
                {
                    'disease': 'Requires Clinical Evaluation',
                    'probability': 0.10,
                    'confidence': 'low',
                    'explanation': 'Further diagnostic workup needed'
                }
            ]
        
        return diagnoses[:3]
    
    def _calculate_triage(self, patient: PatientProfile, diagnoses: List[Dict]) -> int:
        """FIXED: More accurate triage calculation"""
        all_text = ' '.join(
            patient.symptoms + 
            [d['disease'] for d in diagnoses] +
            [d.get('explanation', '') for d in diagnoses]
        ).lower()
        
        # Check for emergency keywords first
        for level in [1, 2, 3]:  # Only check emergency levels
            criteria = self.TRIAGE_CRITERIA[level]
            if any(kw in all_text for kw in criteria['keywords']):
                return level
        
        # Severity-based triage - FIXED logic
        if patient.severity:
            severity_str = patient.severity.lower()
            
            # Extract numeric score
            severity_match = re.search(r'(\d+)', patient.severity)
            if severity_match:
                score = int(severity_match.group(1))
                if score >= 9:
                    return 2  # Urgent
                elif score >= 7:
                    return 3  # Priority
                elif score >= 5:
                    return 4  # Routine
                else:
                    return 5  # Non-urgent
            
            # Text-based severity
            if 'severe' in severity_str:
                return 2
            elif 'moderate' in severity_str:
                return 4
            elif 'mild' in severity_str:
                return 5
        
        # Duration-based adjustment for fever
        if 'fever' in all_text:
            duration_str = (patient.duration or '').lower()
            if any(term in duration_str for term in ['day', 'days', '1', '2', '3']):
                # Short duration fever - routine care
                return 5
            else:
                # Prolonged fever - more urgent
                return 4
        
        return 5  # Default: non-urgent
    
    def _route_department(self, patient: PatientProfile, diagnoses: List[Dict]) -> str:
        all_text = ' '.join(
            patient.symptoms + 
            [d['disease'] for d in diagnoses] +
            [d.get('explanation', '') for d in diagnoses]
        ).lower()
        
        if patient.is_pregnant:
            return "Obstetrics & Gynecology"
        
        scores = {}
        for dept, keywords in self.DEPARTMENT_ROUTING.items():
            score = sum(1 for kw in keywords if kw in all_text)
            if score > 0:
                scores[dept] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return "General Medicine"
    
    def _get_triage_message(self, level: int) -> str:
        messages = {
            1: "🚨 IMMEDIATE EMERGENCY - Call 911 or go to ER NOW",
            2: "⚠️ URGENT - Seek emergency care within 1 hour",
            3: "⚠️ PRIORITY - See a doctor within 24 hours",
            4: "ℹ️ ROUTINE - Schedule appointment within 3-7 days",
            5: "ℹ️ NON-URGENT - Routine checkup when convenient"
        }
        return messages.get(level, "")


# [Rest of the code - ReportGenerator, MedicalOrchestrator, and main() remain the same]

class ReportGenerator:
    """Generate final patient report"""
    
    def generate_report(
        self, 
        patient: PatientProfile,
        diagnosis_result: Dict,
        conversation_history: List[Dict]
    ) -> str:
        report = []
        report.append("="*70)
        report.append("PATIENT MEDICAL ASSESSMENT REPORT")
        report.append("="*70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("PATIENT INFORMATION:")
        report.append("-" * 70)
        if patient.name:
            report.append(f"Name: {patient.name}")
        
        # Show if declined
        if patient.age:
            report.append(f"Age: {patient.age}")
        else:
            report.append(f"Age: Not provided (patient declined)")
        
        if patient.gender:
            report.append(f"Gender: {patient.gender}")
        else:
            report.append(f"Gender: Not provided (patient declined)")
        
        if patient.is_pregnant is not None:
            report.append(f"Pregnant: {'Yes' if patient.is_pregnant else 'No'}")
        report.append("")
        
        report.append("CHIEF COMPLAINTS:")
        report.append("-" * 70)
        for i, symptom in enumerate(patient.symptoms, 1):
            report.append(f"  {i}. {symptom.title()}")
        report.append("")
        
        report.append("SYMPTOM DETAILS:")
        report.append("-" * 70)
        report.append(f"Duration: {patient.duration if patient.duration else 'Not specified'}")
        report.append(f"Severity: {patient.severity if patient.severity else 'Not specified'}")
        report.append("")
        
        if patient.medical_history and any(patient.medical_history):
            report.append("MEDICAL HISTORY:")
            report.append("-" * 70)
            for item in patient.medical_history:
                if item and item.lower() not in ['no', 'none']:
                    report.append(f"  • {item}")
            report.append("")
        
        report.append("CLINICAL ASSESSMENT:")
        report.append("="*70)
        
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
        
        report.append("TRIAGE ASSESSMENT:")
        report.append("-" * 70)
        level = diagnosis_result['triage_level']
        report.append(f"Urgency Level: {level}/5")
        report.append(f"Recommendation: {diagnosis_result['triage_message']}")
        report.append("")
        
        report.append("CARE PATHWAY:")
        report.append("-" * 70)
        report.append(f"Recommended Department: {diagnosis_result['department']}")
        report.append("")
        
        report.append("="*70)
        report.append("IMPORTANT MEDICAL DISCLAIMER:")
        report.append("-" * 70)
        report.append("This is an AI-assisted preliminary assessment and does NOT constitute")
        report.append("professional medical advice, diagnosis, or treatment.")
        report.append("="*70)
        
        return "\n".join(report)


class MedicalOrchestrator:
    """Main orchestrator that coordinates everything"""
    
    def __init__(self, model_name: str = "medllama2"):
        print("\n" + "="*70)
        print("INITIALIZING MEDICAL DIAGNOSTIC SYSTEM")
        print("="*70)
        
        print("\n1. Connecting to Ollama...")
        self.ollama = OllamaClient(model_name=model_name)
        
        print("2. Loading symptom extractor...")
        self.symptom_extractor = SymptomExtractor()
        
        print("3. Initializing question generator...")
        self.question_generator = QuestionGenerator(self.ollama)
        
        print("4. Loading information parser...")
        self.info_parser = InformationParser(self.symptom_extractor)
        
        print("5. Initializing diagnosis engine...")
        self.diagnosis_engine = DiagnosisEngine(self.ollama)
        
        print("6. Loading report generator...")
        self.report_generator = ReportGenerator()
        
        self.reset()
        
        print("\n" + "="*70)
        print("✅ SYSTEM READY")
        print("="*70 + "\n")
    
    def reset(self):
        self.patient = PatientProfile()
        self.state = ConversationState()
        self.conversation_history = []
    
    def chat(self, user_input: str) -> Tuple[str, bool, Optional[str]]:
        self.state.turn_count += 1
        
        self.conversation_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # NEW: Validate ONLY the first user message (when no symptoms collected yet)
        if self.state.is_first_user_message:
            self.state.is_first_user_message = False
            print(f"[DEBUG] Validating first user input: {user_input[:50]}")
            
            is_valid, validation_message = self._validate_initial_input(user_input)
            
            if not is_valid:
                print(f"[DEBUG] Invalid initial input detected, ending conversation")
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': validation_message
                })
                return validation_message, True, None  # End conversation
            else:
                print(f"[DEBUG] Valid medical input detected, continuing")
        
        # Parse information
        self.info_parser.parse_response(user_input, self.patient, self.state)
        
        # Get current missing info
        missing = self.state.get_missing_info()
        print(f"[DEBUG] After parsing - Missing: {missing}, Collected: {self.state.collected}")
        
        # Check if user just answered a symptom-specific question
        if (not missing and
            self.state.symptom_question_attempts > 0 and
            self.state.symptom_specific_questions_asked < self.state.max_symptom_questions and
            len(user_input.strip()) > 3):
            
            print(f"[DEBUG] User answered symptom question, moving to next")
            self.state.mark_symptom_question_asked()
        
        # Check if ready to diagnose
        print(f"[DEBUG] Checking if complete: is_complete={self.state.is_complete()}")
        if self.state.is_complete():
            print("[DEBUG] System is complete, finalizing diagnosis")
            return self._finalize_diagnosis()
        
        # Generate next question
        print("[DEBUG] Generating next question...")
        question = self.question_generator.generate_question(
            self.state,
            self.patient,
            user_input
        )
        
        print(f"[DEBUG] Generated question: {question if question else 'None - should diagnose or continue'}")
        
        # Handle None from auto-skip or completion
        if question is None:
            if self.state.is_complete():
                print("[DEBUG] No question generated and complete, forcing diagnosis")
                return self._finalize_diagnosis()
            else:
                print("[DEBUG] No question generated, generating next one")
                question = self.question_generator.generate_question(
                    self.state,
                    self.patient,
                    user_input
                )
                
                if question is None:
                    print("[DEBUG] Still no question after retry, forcing diagnosis")
                    return self._finalize_diagnosis()
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': question
        })
        
        return question, False, None
    
    def _validate_initial_input(self, user_input: str) -> Tuple[bool, str]:
        """
        Validate that the initial user input is medical-related.
        Returns: (is_valid, message)
        """
        user_input_lower = user_input.lower().strip()
        
        # Check if it's too short (likely not a symptom description)
        if len(user_input_lower) < 5:
            return False, "⚠️ Please describe your medical symptoms or health concerns. This system is designed for medical symptom assessment only."
        
        # Extract symptoms from input
        symptoms = self.symptom_extractor.extract(user_input)
        
        # If symptoms found, input is valid
        if symptoms:
            print(f"[DEBUG] Valid medical input detected. Symptoms: {symptoms}")
            return True, ""
        
        # Check for common non-medical patterns
        non_medical_patterns = [
            # Math/calculations
            r'\d+\s*[\+\-\*\/×÷]\s*\d+',  # 95*96, 5+5, etc.
            r'what is \d+',
            r'calculate',
            r'solve',
            r'equation',
            r'answer',
            
            # Greetings/casual (but allow if combined with symptoms)
            r'^(hi|hello|hey|good morning|good evening|sup|yo)$',
            
            # Questions about the system
            r'what can you do',
            r'how do you work',
            r'who are you',
            r'what are you',
            r'your capabilities',
            r'your purpose',
            
            # Random queries
            r'weather',
            r'\btime\b',
            r'\bdate\b',
            r'news',
            r'sports',
            r'joke',
            r'story',
            r'recipe',
            r'cooking',
            r'directions',
            r'navigate',
            r'movie',
            r'music',
            r'game',
        ]
        
        for pattern in non_medical_patterns:
            if re.search(pattern, user_input_lower):
                print(f"[DEBUG] Non-medical pattern detected: {pattern}")
                return False, self._get_rejection_message()
        
        # Check for medical keywords that might not be in symptom database
        medical_keywords = [
            'pain', 'hurt', 'ache', 'sore', 'sick', 'ill', 'unwell', 'feel',
            'symptom', 'problem', 'issue', 'concern', 'worried', 'doctor',
            'hospital', 'medicine', 'medication', 'treatment', 'diagnosis',
            'suffering', 'uncomfortable', 'discomfort', 'bad', 'terrible',
            'awful', 'worse', 'better', 'injury', 'injured', 'wound',
            'bleeding', 'swollen', 'infected', 'infection', 'disease',
            'condition', 'health', 'medical', 'emergency', 'urgent'
        ]
        
        if any(keyword in user_input_lower for keyword in medical_keywords):
            print(f"[DEBUG] Medical keyword found, accepting input")
            return True, ""
        
        # If no symptoms and no medical keywords found, reject
        print(f"[DEBUG] No medical content detected in: {user_input}")
        return False, self._get_rejection_message()
    
    def _get_rejection_message(self) -> str:
        """Generate a polite rejection message for non-medical queries"""
        return """⚠️ I'm a medical symptom assessment assistant and can only help with health-related concerns.

Please describe your medical symptoms or health issues, such as:
- Physical symptoms (pain, fever, nausea, dizziness, etc.)
- How long you've been experiencing them
- Any concerns about your health

Examples of valid queries:
✅ "I have a headache and fever"
✅ "I'm feeling dizzy and nauseous"
✅ "I have chest pain that started this morning"
✅ "My stomach hurts and I've been vomiting"
✅ "I'm experiencing shortness of breath"

For non-medical questions, please use a general-purpose assistant.

Thank you for understanding! 🏥"""
    
    def _finalize_diagnosis(self) -> Tuple[str, bool, str]:
        print("\n[Generating diagnosis...]")
        
        # Add safety check
        if not self.patient.symptoms:
            print("[ERROR] No symptoms collected, cannot diagnose")
            return "I'm sorry, I couldn't collect enough information about your symptoms. Please start over and describe your symptoms.", True, None
        
        diagnosis_result = self.diagnosis_engine.diagnose(self.patient)
        report = self.report_generator.generate_report(
            self.patient,
            diagnosis_result,
            self.conversation_history
        )
        
        response = self._create_summary_response(diagnosis_result)
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': response
        })
        
        return response, True, report
    
    def _create_summary_response(self, diagnosis_result: Dict) -> str:
        lines = []
        lines.append("\nThank you for providing that information. Based on our conversation, here is my medical assessment:\n")
        lines.append("="*70)
        lines.append("MEDICAL ASSESSMENT")
        lines.append("="*70 + "\n")
        
        lines.append("📋 SYMPTOMS REPORTED:")
        for symptom in self.patient.symptoms:
            lines.append(f"   • {symptom.title()}")
        lines.append("")
        
        lines.append("🔍 DIFFERENTIAL DIAGNOSES:\n")
        for i, diag in enumerate(diagnosis_result['diagnoses'], 1):
            prob = diag['probability'] * 100
            lines.append(f"   {i}. {diag['disease']} ({prob:.1f}% probability)")
            if 'explanation' in diag and diag['explanation']:
                lines.append(f"      → {diag['explanation']}")
            lines.append("")
        
        lines.append(f"🏥 RECOMMENDED DEPARTMENT: {diagnosis_result['department']}\n")
        
        level = diagnosis_result['triage_level']
        message = diagnosis_result['triage_message']
        lines.append(f"⚠️  URGENCY ASSESSMENT:")
        lines.append(f"    Level: {level}/5")
        lines.append(f"    Action: {message}\n")
        
        lines.append("="*70)
        lines.append("⚠️  DISCLAIMER: This is a preliminary AI assessment, not a medical diagnosis.")
        lines.append("="*70)
        
        return "\n".join(lines)
    
    def get_diagnosis_data(self) -> Dict:
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


def main():
    import sys
    
    try:
        orchestrator = MedicalOrchestrator(model_name="medllama2")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    
    print("\nBot: Hello! I'm here to help assess your symptoms.")
    print("     What brings you here today?\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                break
            
            if not user_input:
                continue
            
            response, is_final, report = orchestrator.chat(user_input)
            print(f"\nBot: {response}\n")
            
            if is_final:
                show = input("\n📄 See full report? (y/n): ").lower()
                if show == 'y':
                    print("\n" + report)
                break
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()