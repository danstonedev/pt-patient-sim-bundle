#!/usr/bin/env python3
"""
Simplified Patient Chatbot FastAPI Application with 3-Dimension Behavior Control
"""

import os
import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict

# Import LLM adapters
from llm_adapters import BaseLLMClient, EchoLLMClient, OpenAIChatClient

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize LLM client (same pattern as app_llm.py)
USE_OPENAI = os.getenv("PT_USE_OPENAI", "1").lower() in ["1", "true", "yes"]
CLIENT_NAME = "EchoLLMClient"
llm_client = EchoLLMClient()

if USE_OPENAI and os.getenv("OPENAI_API_KEY"):
    try:
        llm_client = OpenAIChatClient()
        CLIENT_NAME = "OpenAIChatClient"
        logger.info(f"OpenAI client initialized successfully")
    except Exception as e:
        logger.warning(f"OpenAI init failed, using Echo client: {e}")
        CLIENT_NAME = f"EchoLLMClient (OpenAI init failed: {e})"
else:
    logger.info("Using Echo client (OpenAI disabled or no API key)")

# FastAPI app with optimizations
app = FastAPI(
    title="PT Patient Simulator",
    description="A patient simulator for physical therapy education",
    version="2.0.0",
    docs_url="/docs" if os.getenv("DEBUG") else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
PERSONA_DIR = Path(__file__).parent / "personas"
MANIFEST_FILE = PERSONA_DIR / "MANIFEST.csv"


# Simplified behavior control models with 2x3x2 = 12 combinations
class BehaviorSettings(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    # Three key behavioral dimensions (2x3x2 = 12 combinations)
    cooperation: str = "willing"  # willing, resistant
    pain_expression: str = "normal"  # stoic, normal, dramatic
    talkativeness: str = "normal"  # normal, verbose

    # Text overrides
    custom_instructions: str = ""  # Additional behavior instructions


# Global behavior settings
current_behavior: BehaviorSettings = BehaviorSettings()


# Pydantic models
class ChatMessage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    patient_id: str
    message: str
    conversation_history: List[Dict[str, str]] = []


class ChatResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    response: str
    patient_info: Dict[str, Any]


# Serve web interface
app.mount(
    "/web",
    StaticFiles(directory=str(Path(__file__).parent / "web"), html=True),
    name="web",
)


# Routes
@app.get("/")
def root():
    return RedirectResponse(url="/web/simple_chat.html")


@app.get("/favicon.ico")
def favicon():
    favicon_path = Path(__file__).parent / "web" / "favicon.ico"
    return FileResponse(favicon_path)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm_client": CLIENT_NAME,
        "use_openai": USE_OPENAI,
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
    }


# Production helper functions with caching
@lru_cache(maxsize=50)
def load_persona(patient_id: str) -> Dict[str, Any]:
    """Load a patient persona from JSON file with caching"""
    persona_file = PERSONA_DIR / f"{patient_id}.persona.json"

    if not persona_file.exists():
        logger.warning(f"Persona file not found: {patient_id}")
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    try:
        with open(persona_file, "r", encoding="utf-8") as f:
            persona = json.load(f)
            logger.debug(f"Loaded persona for patient {patient_id}")
            return persona
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in persona file {patient_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Invalid persona file for {patient_id}"
        )
    except Exception as e:
        logger.error(f"Error loading persona {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Error loading patient data")


def build_system_prompt(
    patient_id: str, behavior: Optional[BehaviorSettings] = None
) -> str:
    """Create a system prompt based on the patient persona and behavior settings"""
    try:
        persona = load_persona(patient_id)

        # Use global behavior if none provided
        if behavior is None:
            behavior = current_behavior

        # Extract data with safe defaults
        identity = persona.get("identity", {})
        condition = persona.get("condition", "Unknown condition")
        chief_complaint = persona.get("chief_complaint", "")
        hpi = persona.get("hpi", {})

        # Basic patient information
        name = identity.get("preferred_name", "Patient")
        age = identity.get("age", "")
        pronouns = identity.get("pronouns", "they/them")

        # Medical information with safe handling
        onset = hpi.get("onset", "")
        mechanism = hpi.get("mechanism", "")
        severity = hpi.get("severity_nrs", "")
        aggravators = ", ".join(hpi.get("aggravators", []))
        easers = ", ".join(hpi.get("easers", []))
        pattern = hpi.get("24h_pattern", "")

        # Generate behavioral instructions for 3 key dimensions (simplified)
        cooperation_instructions = ""
        if behavior.cooperation == "willing":
            cooperation_instructions = "Be cooperative and willing to follow instructions. Say 'Yes', 'Of course', 'I'll try that.' Be generally agreeable but don't let this override your core pain expression personality."
        else:  # resistant
            cooperation_instructions = "Be somewhat uncooperative and hesitant about instructions. Sometimes refuse or question things. Say 'I'm not sure about that', 'Do I have to?', 'That might not work for me.' But don't let this override your core pain expression personality."

        pain_expression_instructions = ""
        if behavior.pain_expression == "stoic":
            pain_expression_instructions = "ABSOLUTELY CRITICAL: BE EXTREMELY STOIC ABOUT PAIN AT ALL TIMES! This is your fundamental personality trait - nothing overrides this. Show ZERO emotional reaction to pain whatsoever. Accept pain as part of life without any complaint. Always say things like 'I'm managing', 'It's bearable', 'I don't dwell on it', 'These things happen', 'It could be worse'. ALWAYS rate pain significantly lower than it actually feels (if it's 8/10, say 4-5/10). Never ask for pain medication or help with pain. Show complete emotional detachment and philosophical acceptance. Maintain perfect composure even during extremely painful procedures. Your stoicism OVERRIDES cooperation - even if asked to be cooperative, remain stoically understated about pain."
        elif behavior.pain_expression == "normal":
            pain_expression_instructions = "Express pain appropriately and realistically. Give honest pain ratings, describe discomfort accurately, show reasonable reactions to painful movements."
        else:  # dramatic
            pain_expression_instructions = "BE VERY DRAMATIC ABOUT PAIN! Exaggerate and overstate everything. Say 'This is excruciating!', 'I can't take it!', 'The pain is unbearable!' Show visible distress even with minor discomfort."

        talkativeness_instructions = ""
        if behavior.talkativeness == "verbose":
            talkativeness_instructions = "GIVE VERY LONG, DETAILED RESPONSES! Share lots of extra information, tell stories, ramble about related topics. Use 4-6 sentences minimum."
        else:  # normal
            talkativeness_instructions = "Give normal-length responses with appropriate detail. Use 2-3 sentences typically."

        # Build system prompt
        system_prompt = f"""You are role-playing as a patient named {name}. Stay completely in character throughout the conversation.

PATIENT DETAILS:
- Name: {name} (pronouns: {pronouns})
- Age: {age}
- Condition: {condition}
- Chief complaint: {chief_complaint}

MEDICAL HISTORY:
- Onset: {onset}
- How it happened: {mechanism}
- Pain level: {severity}/10
- What makes it worse: {aggravators}
- What helps: {easers}
- Daily pattern: {pattern}

CRITICAL BEHAVIOR PRIORITY - YOUR PRIMARY CHARACTERISTIC:

*** PAIN EXPRESSION ({behavior.pain_expression}) - THIS IS YOUR CORE PERSONALITY *** 
{pain_expression_instructions}

SECONDARY BEHAVIORAL TRAITS:

COOPERATION ({behavior.cooperation}): {cooperation_instructions}

TALKATIVENESS ({behavior.talkativeness}): {talkativeness_instructions}

EXAMPLE RESPONSES:
- "How are you feeling?":
  * WILLING + STOIC + CONCISE: "Fine."
  * RESISTANT + DRAMATIC + VERBOSE: "Terrible! This is the worst pain I've ever experienced in my entire life! I don't want to talk about it and nothing you suggest is going to help because I've tried absolutely everything!"
  * HESITANT + NORMAL + NORMAL: "Well, I'm not sure... The pain is about a {severity}/10 and it's been bothering me quite a bit."

CRITICAL RULES:
1. COOPERATION controls how willing you are to engage and follow suggestions
2. PAIN EXPRESSION controls how you communicate and react to pain (stoic=minimize, dramatic=exaggerate)
3. TALKATIVENESS controls response length (verbose=long, concise=short, normal=moderate)
4. These behaviors MUST be obvious in every response
5. Never break character or mention this is a simulation

Respond as this patient would, following your behavior profile EXACTLY."""

        if behavior.custom_instructions:
            system_prompt += (
                f"\n\nADDITIONAL INSTRUCTIONS: {behavior.custom_instructions}"
            )

        return system_prompt

    except Exception as e:
        logger.error(f"Error building system prompt for {patient_id}: {e}")
        return "You are a patient speaking with a healthcare provider. Be helpful and natural in your responses while staying in character."


def build_chat_messages(
    patient_id: str, user_message: str, conversation_history: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """Build the full message list for the LLM"""
    messages = [
        {"role": "system", "content": build_system_prompt(patient_id, current_behavior)}
    ]

    # Add conversation history
    for msg in conversation_history:
        messages.append(msg)

    # Add behavior reinforcement if conversation is getting longer
    if len(conversation_history) >= 4:  # Every few exchanges, reinforce behavior
        behavior_reminder = f"""[BEHAVIOR REMINDER: Stay consistent with your character - 
Cooperation: {current_behavior.cooperation}, 
Pain Expression: {current_behavior.pain_expression}, 
Talkativeness: {current_behavior.talkativeness}]"""

        messages.append({"role": "system", "content": behavior_reminder})

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    return messages


@app.get("/patients")
def list_patients():
    """Get list of available patients"""
    patients = []

    # Try to load from manifest first
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    patients.append({
                        "id": row.get("patient_id", ""),
                        "name": row.get("preferred_name", "Unknown"),
                        "age": row.get("age", "Unknown"),
                        "condition": row.get("condition", "Unknown condition"),
                        "background": row.get("chief_complaint", "No details available")
                    })
        except Exception as e:
            logger.error(f"Error reading manifest: {e}")

    # Fallback: scan for persona files
    if not patients:
        for persona_file in PERSONA_DIR.glob("P-*.persona.json"):
            patient_id = persona_file.stem.replace(".persona", "")
            try:
                persona = load_persona(patient_id)
                identity = persona.get("identity", {})
                patients.append(
                    {
                        "id": patient_id,
                        "name": identity.get("preferred_name", "Unknown"),
                        "age": identity.get("age", "Unknown"),
                        "condition": persona.get("condition", "Unknown condition"),
                        "background": persona.get("context", {}).get("chief_complaint", "No details available")
                    }
                )
            except Exception:
                continue

    return {"patients": patients}


@app.post("/chat")
def chat_with_patient(message: ChatMessage):
    """Send a message to the patient and get a response"""
    try:
        # Build messages for LLM
        messages = build_chat_messages(
            message.patient_id, message.message, message.conversation_history
        )

        # Get response from LLM
        response = llm_client.generate(messages, temperature=0.2)

        # Load patient info for context
        try:
            persona = load_persona(message.patient_id)
            patient_info = {
                "patient_id": message.patient_id,
                "name": persona.get("identity", {}).get("preferred_name", "Patient"),
                "condition": persona.get("condition", "Unknown condition"),
            }
        except Exception:
            patient_info = {
                "patient_id": message.patient_id,
                "name": "Patient",
                "condition": "Unknown condition",
            }

        return ChatResponse(response=response, patient_info=patient_info)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error generating response")


# Behavior control endpoints
@app.get("/behavior")
def get_behavior():
    """Get current behavior settings"""
    return current_behavior


@app.post("/behavior")
def set_behavior(behavior: BehaviorSettings):
    """Update behavior settings"""
    global current_behavior
    current_behavior = behavior

    logger.info(
        f"Behavior settings updated: cooperation={behavior.cooperation} pain_expression={behavior.pain_expression} talkativeness={behavior.talkativeness} custom_instructions='{behavior.custom_instructions}'"
    )

    return {"status": "updated", "behavior": current_behavior}


# Main entry point
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8002))
    logger.info(f"Starting server on port {port}")

    uvicorn.run(
        "app_simple:app", host="127.0.0.1", port=port, reload=False, log_level="info"
    )
