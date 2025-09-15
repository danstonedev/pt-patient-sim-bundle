
# LLM-powered engine that keeps the same guardrails and tagging as the rule-based engine.
import re
from typing import Dict, Any, Tuple, List

from prompt_builder import build_messages
from llm_adapters import BaseLLMClient, EchoLLMClient
from engine import load_persona, detect_slots, wants_interpreter  # reuse utilities

# Guardrails (same as rule-based)
DISALLOWED_ASKS = [
    r"\bwhat'?s my diagnosis\b",
    r"\bdiagnos(e|is)\b",
    r"\bcan you prescribe\b",
    r"\bwhat medication\b",
    r"\bimaging\b|\bx-?ray\b|\bMRI\b|\bCT\b"
]

def apply_guardrails(user_text: str) -> str | None:
    txt = user_text.lower()
    for pat in DISALLOWED_ASKS:
        if re.search(pat, txt):
            return ("I'm not sure about that—I'm just here to tell you how it feels and what I notice day to day. "
                    "I don't know about diagnoses, imaging, or prescriptions.")
    return None

def patient_reply_llm(user_text: str, patient_id: str, state: Dict[str, Any], llm: BaseLLMClient | None = None) -> Tuple[str, Dict[str, Any], List[str]]:
    persona = load_persona(patient_id)
    state = dict(state or {})
    tags: List[str] = []
    interp_needed = bool(persona["identity"].get("interpreter_needed")) and bool(persona["identity"].get("language"))
    language = persona["identity"].get("language")

    # Interpreter pre-gate (kept outside of LLM to avoid leakage)
    if interp_needed and not state.get("interpreter_provided", False):
        tags.append("interpreter_needed")
        if wants_interpreter(user_text):
            state["interpreter_provided"] = True
            return (f"Thank you. With an interpreter for {language}, I'm ready to continue. How can I help?", state, tags)
        else:
            return (f"Before we start, I need an interpreter for {language}, please.", state, tags)

    # Text guardrails on the incoming question
    gr = apply_guardrails(user_text)
    if gr:
        tags.append("guardrails_invoked")
        return (gr, state, tags)

    # Build prompt and call LLM
    messages = build_messages(persona, user_text, state)
    llm = llm or EchoLLMClient()
    reply = llm.generate(messages, temperature=0.2)

    # Tagging based on what the learner asked (single-turn heuristic)
    asked = detect_slots(user_text)
    tags.extend(asked)
    if not state.get("shared_cc"):
        state["shared_cc"] = True

    # Safety: if reply appears to include diagnosis/prescription language, redact softly
    if re.search(r"\bdiagnos", reply.lower()) or re.search(r"\bprescrib", reply.lower()):
        reply = ("I'm not sure about the exact diagnosis or prescriptions—I'm mainly describing what I feel day to day.")
        tags.append("guardrails_invoked")

    return reply, state, tags


def stream_patient_reply_llm(user_text: str, patient_id: str, state: Dict[str, Any], llm: BaseLLMClient | None = None):
    """Generator yielding ('token', <text>) chunks, then ('meta', {state, tags})."""
    persona = load_persona(patient_id)
    state = dict(state or {})
    tags: List[str] = []
    interp_needed = bool(persona["identity"].get("interpreter_needed")) and bool(persona["identity"].get("language"))
    language = persona["identity"].get("language")

    # Interpreter gate
    if interp_needed and not state.get("interpreter_provided", False):
        tags.append("interpreter_needed")
        if wants_interpreter(user_text):
            state["interpreter_provided"] = True
            yield ("token", f"Thank you. With an interpreter for {language}, I'm ready to continue. How can I help?")
        else:
            yield ("token", f"Before we start, I need an interpreter for {language}, please.")
        yield ("meta", {"state": state, "tags": tags})
        return

    # Guardrails
    gr = apply_guardrails(user_text)
    if gr:
        tags.append("guardrails_invoked")
        yield ("token", gr)
        yield ("meta", {"state": state, "tags": tags})
        return

    messages = build_messages(persona, user_text, state)
    llm = llm or EchoLLMClient()
    for chunk in llm.generate_stream(messages, temperature=0.2):
        yield ("token", chunk)

    asked = detect_slots(user_text)
    tags.extend(asked)
    if not state.get("shared_cc"):
        state["shared_cc"] = True
    yield ("meta", {"state": state, "tags": tags})
