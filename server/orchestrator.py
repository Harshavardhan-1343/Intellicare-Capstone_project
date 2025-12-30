import requests
import json
import re
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class PatientProfile:
    """Patient information structure"""
    age: Optional[int] = None
    gender: Optional[str] = None
    symptoms: List[str] = field(default_factory=list)
    duration: Optional[str] = None
    severity: Optional[str] = None
    medical_history: List[str] = field(default_factory=list)
    is_pregnant: Optional[bool] = None
    
    # Temporary buffer for raw text answers before LLM processing
    raw_answers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self):
        d = {k: v for k, v in self.__dict__.items() if k != 'raw_answers'}
        return d


class OllamaClient:
    """Robust Ollama Client"""
    
    def __init__(self, model_name="medllama2", base_url="http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self._verify_connection()
    
    def _verify_connection(self):
        try:
            requests.get(f"{self.base_url}/api/tags", timeout=5)
            print(f"✓ Connected to Ollama at {self.base_url}")
        except Exception as e:
            raise ConnectionError(f"Cannot connect to Ollama: {e}\nPlease run 'ollama serve'")

    def generate(self, prompt: str, max_tokens: int = 250, temperature: float = 0.1, json_mode: bool = False) -> str:
        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "stop": ["\n\n", "User:", "Assistant:", "Doctor:", "Patient:", "System:"]
        }
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": options
        }
        if json_mode:
            payload["format"] = "json"
            
        try:
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()["response"].strip()
        except Exception as e:
            print(f"[LLM Error] {e}")
            return ""


class ConversationState:
    """Manages the strict flow of the conversation"""
    
    BASIC_FLOW = [
        'symptoms_init',
        'age',
        'gender',
        'duration',
        'severity',
        'history'
    ]
    
    def __init__(self):
        self.step_index = 0
        self.basic_info_complete = False
        self.symptom_questions_asked = 0
        self.max_symptom_questions = 3
        self.generated_questions = []
        
    def get_current_step(self) -> str:
        if self.step_index < len(self.BASIC_FLOW):
            return self.BASIC_FLOW[self.step_index]
        return "dynamic_phase"
        
    def advance_step(self):
        self.step_index += 1
        if self.step_index >= len(self.BASIC_FLOW):
            self.basic_info_complete = True


class InformationParser:
    """Handles extracting information from user responses."""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client

    def batch_process_profile(self, patient: PatientProfile) -> None:
        print("[DEBUG] Running Batch Processing on collected data...")
        
        raw = patient.raw_answers
        raw_text_block = "\n".join([f"- {k.upper()}: {v}" for k, v in raw.items() if v])
        
        prompt = f"""
        You are a medical data entry assistant. 
        Analyze the following RAW PATIENT INPUTS and convert them into a standard JSON format.
        
        RAW PATIENT INPUTS:
        {raw_text_block}
        
        INSTRUCTIONS:
        1. Extract symptoms into a list.
        2. Age: Convert to integer.
        3. Gender: Standardize to "Male", "Female", or "Other".
        4. Duration: Standardize (e.g., "2 weeks").
        5. Severity: Standardize (e.g., "Moderate" or "5/10").
        6. Medical History: List distinct conditions. If user said "no", "none", return [].
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "symptoms": ["<extracted_symptom_1>", "<extracted_symptom_2>"],
            "age": <extracted_age_int>,
            "gender": "<extracted_gender>",
            "duration": "<extracted_duration>",
            "severity": "<extracted_severity>",
            "medical_history": ["<condition1>", "<condition2>"]
        }}
        """
        
        response = self.ollama.generate(prompt, max_tokens=300, temperature=0.0, json_mode=True)
        self._apply_json_update(patient, response, raw)

    def update_dynamic_profile(self, patient: PatientProfile, user_text: str) -> None:
        if len(user_text.split()) < 4 and any(w in user_text.lower() for w in ['no', 'none', 'nope', 'nothing']):
            return

        prompt = f"""
        Extract any NEW symptoms mentioned in this text into a JSON list.
        Input: "{user_text}"
        Output: {{ "new_symptoms": ["symptom1", "symptom2"] }}
        """
        response = self.ollama.generate(prompt, max_tokens=100, temperature=0.0, json_mode=True)
        
        try:
            data = json.loads(response)
            if "new_symptoms" in data and isinstance(data["new_symptoms"], list):
                for s in data["new_symptoms"]:
                    if s and s.lower() not in patient.symptoms:
                        patient.symptoms.append(str(s).lower())
        except:
            pass

    def _apply_json_update(self, patient, response, raw_fallback):
        try:
            data = json.loads(response)
            if data.get('age'): patient.age = data['age']
            if data.get('gender'): patient.gender = data['gender']
            if data.get('duration'): patient.duration = data['duration']
            if data.get('severity'): patient.severity = data['severity']
            
            if data.get('symptoms'):
                current = set(patient.symptoms)
                for s in data['symptoms']:
                    if s: current.add(str(s).lower())
                patient.symptoms = list(current)
                
            if 'medical_history' in data:
                raw_hist = data['medical_history']
                if isinstance(raw_hist, list):
                    patient.medical_history = [str(x) for x in raw_hist if x and str(x).lower() not in ['no', 'none', 'null']]
                    
        except json.JSONDecodeError:
            print("[ERROR] JSON Parse Error. Applying Fallback.")
            if not patient.age and raw_fallback.get('age', '').isdigit():
                patient.age = int(raw_fallback['age'])
            if not patient.gender: patient.gender = raw_fallback.get('gender')
            if not patient.duration: patient.duration = raw_fallback.get('duration')
            if not patient.severity: patient.severity = raw_fallback.get('severity')


class DiagnosisEngine:
    """Handles medical logic"""
    
    # RESTORED: Hardcoded Triage Logic
    TRIAGE_MESSAGES = {
        1: "🚨 IMMEDIATE EMERGENCY - Call 911 or go to ER NOW",
        2: "⚠️ URGENT - Seek emergency care within 1 hour",
        3: "⚠️ PRIORITY - See a doctor within 24 hours",
        4: "ℹ️ ROUTINE - Schedule appointment within 3-7 days",
        5: "ℹ️ NON-URGENT - Routine checkup when convenient"
    }
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    def _safe_join(self, items: List[Any]) -> str:
        if not items: return "None"
        return ', '.join([str(x) for x in items if x])

    def generate_followup(self, patient: PatientProfile, prev_questions: List[str]) -> str:
        history_str = self._safe_join(patient.medical_history)
        symptoms_str = self._safe_join(patient.symptoms)
        prev_q_str = "\n".join([f"- {q}" for q in prev_questions]) if prev_questions else "None"
        forbidden = f"{symptoms_str}, age, gender, duration, severity, history"
        
        prompt = f"""
        You are a medical assistant talking DIRECTLY to a patient.
        
        PATIENT CONTEXT:
        - Known Symptoms: {symptoms_str}
        - Age/Gender: {patient.age}/{patient.gender}
        - Duration: {patient.duration}
        
        PREVIOUSLY ASKED:
        {prev_q_str}
        
        TASK:
        Ask ONE SPECIFIC Yes/No or descriptive question to check for a symptom NOT listed above. 
        Think of a differential diagnosis and ask a distinguishing question.
        
        STRICT RULES:
        1. Use "You" (e.g., "Do you have a stiff neck?").
        2. DO NOT ask "What other symptoms do you have?". BE SPECIFIC.
        3. DO NOT ask about {forbidden}.
        4. Return ONLY the question.
        
        QUESTION:
        """
        
        raw_response = self.ollama.generate(prompt, max_tokens=60, temperature=0.6)
        return self._clean_llm_question(raw_response)

    def _clean_llm_question(self, text: str) -> str:
        text = text.strip().replace('"', '')
        if ":" in text: text = text.split(":")[-1].strip()
        sentences = re.split(r'(?<=[.!?]) +', text)
        questions = [s for s in sentences if "?" in s]
        return questions[0] if questions else text

    def diagnose(self, patient: PatientProfile) -> Dict:
        prompt = f"""
        Act as a doctor. Analyze this patient:
        {json.dumps(patient.to_dict(), indent=2)}
        
        Provide:
        1. Top 3 Differential Diagnoses with probabilities.
        2. Triage Level (1-5, where 1 is Emergency).
        3. Recommended Medical Department.
        
        Response Format (JSON):
        {{
            "diagnoses": [
                {{"disease": "Name", "probability": 0.8, "explanation": "Brief reason why..."}}
            ],
            "triage_level": 4,
            "department": "General Medicine"
        }}
        """
        try:
            response = self.ollama.generate(prompt, max_tokens=500, temperature=0.2, json_mode=True)
            result = json.loads(response)
            
            # Apply Hardcoded Triage Message
            level = int(result.get('triage_level', 4))
            # Ensure level is 1-5
            level = max(1, min(5, level))
            result['triage_message'] = self.TRIAGE_MESSAGES.get(level, "Consult a doctor")
            result['triage_level'] = level
            
            return result
        except:
            return {
                "diagnoses": [{"disease": "Analysis Incomplete", "probability": 0.0, "explanation": "Error processing"}],
                "triage_level": 3,
                "department": "General Medicine",
                "triage_message": self.TRIAGE_MESSAGES[3]
            }


class ReportGenerator:
    """Generates the final report with strict formatting"""
    
    def generate_report(self, patient: PatientProfile, result: Dict) -> str:
        history_display = ', '.join([str(x) for x in patient.medical_history if x]) if patient.medical_history else "None"
        symptoms_display = ', '.join([str(x) for x in patient.symptoms if x])
        
        # RESTORED: Strict Report Format
        lines = [
            "="*60,
            "INTELLICARE MEDICAL REPORT",
            "="*60,
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            
            "PATIENT INFORMATION:",
            "-"*60,
            f"Age:     {patient.age if patient.age else 'Not Provided'}",
            f"Gender:  {patient.gender if patient.gender else 'Not Provided'}",
            f"History: {history_display}",
            "",
            
            "CLINICAL PRESENTATION:",
            "-"*60,
            f"Chief Complaints: {symptoms_display}",
            f"Duration:         {patient.duration}",
            f"Severity:         {patient.severity}",
            "",
            
            "DIFFERENTIAL DIAGNOSIS:",
            "-"*60
        ]
        
        # FIX: Include Explanations
        for i, d in enumerate(result.get('diagnoses', []), 1):
            name = d.get('disease', 'Unknown')
            prob = int(d.get('probability', 0) * 100)
            note = d.get('explanation', 'No details provided.')
            lines.append(f"{i}. {name} ({prob}%)")
            lines.append(f"   Note: {note}")
        
        lines.extend([
            "",
            "TRIAGE ASSESSMENT:",
            "-"*60,
            f"Urgency Level: {result.get('triage_level', '?')}/5",
            f"Action:        {result.get('triage_message', 'Consult a doctor')}",
            f"Department:    {result.get('department', 'General Practice')}",
            "",
            "="*60
        ])
        
        return "\n".join(lines)


class MedicalOrchestrator:
    def __init__(self, model_name: str = "medllama2"):
        self.ollama = OllamaClient(model_name=model_name)
        self.parser = InformationParser(self.ollama)
        self.diagnosis_engine = DiagnosisEngine(self.ollama)
        self.report_generator = ReportGenerator()
        self.reset()
        
    def reset(self):
        self.patient = PatientProfile()
        self.state = ConversationState()
        self.conversation_history = []
        
    def chat(self, user_input: str) -> Tuple[str, bool, Optional[str]]:
        
        # --- PHASE 1: COLLECT BASIC INFO ---
        if not self.state.basic_info_complete:
            # Store answer to PREVIOUS question
            if self.state.step_index == 0:
                self.patient.raw_answers['symptoms_init'] = user_input
                self.patient.symptoms.append(user_input) 
            else:
                prev_step = self.state.BASIC_FLOW[self.state.step_index]
                self.patient.raw_answers[prev_step] = user_input
            
            self.state.advance_step()
            
            if self.state.basic_info_complete:
                self.parser.batch_process_profile(self.patient)
            else:
                return self._get_hardcoded_question(self.state.get_current_step()), False, None

        # --- PHASE 2: DYNAMIC DIAGNOSIS ---
        
        if self.state.symptom_questions_asked > 0:
            self.parser.update_dynamic_profile(self.patient, user_input)

        if self.state.symptom_questions_asked < self.state.max_symptom_questions:
            self.state.symptom_questions_asked += 1
            question = self.diagnosis_engine.generate_followup(
                self.patient, 
                self.state.generated_questions
            )
            self.state.generated_questions.append(question)
            return question, False, None
            
        # --- PHASE 3: FINAL REPORT ---
        return self._finalize_session()

    def _get_hardcoded_question(self, step_name: str) -> str:
        questions = {
            'age': "May I ask how old you are?",
            'gender': "What is your gender?",
            'duration': "How long have you had these symptoms?",
            'severity': "On a scale of 1-10, how severe is the discomfort?",
            'history': "Do you have any past medical conditions (e.g., Diabetes, Asthma)?"
        }
        return questions.get(step_name, "Error: Unknown Step")

    def _finalize_session(self):
        result = self.diagnosis_engine.diagnose(self.patient)
        report = self.report_generator.generate_report(self.patient, result)
        
        response = f"""Based on our assessment:
        
Possible Conditions:
1. {result['diagnoses'][0].get('disease', 'Unknown')}
2. {result['diagnoses'][1].get('disease', 'Unknown') if len(result['diagnoses']) > 1 else '...'}

Recommendation: {result.get('triage_message', 'Consult a doctor.')}
Department: {result.get('department', 'General')}

(See full report for details)"""
        
        return response, True, report

    def get_diagnosis_data(self):
        return self.diagnosis_engine.diagnose(self.patient)