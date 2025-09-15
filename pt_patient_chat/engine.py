
import json
import re
from pathlib import Path
from typing import Dict, Any, Tuple, List

PERSONA_DIR = Path(__file__).resolve().parent / "personas"

# --- Utility: load persona ---
def load_persona(patient_id: str) -> Dict[str, Any]:
    p = PERSONA_DIR / f"{patient_id}.persona.json"
    if not p.exists():
        raise FileNotFoundError(f"Persona not found for {patient_id} at {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

# --- Simple NLU for slot detection ---
SLOTS = {
    "onset": [r"\bonset\b", r"\bstart(ed|)\b", r"\bwhen did\b", r"\bsince\b"],
    "mechanism": [r"\bhow happen(ed|)\b", r"\bmechanism\b", r"\bwhat were you doing\b", r"\binjur(ed|y)\b"],
    "location": [r"\bwhere\b", r"\blocation\b", r"\bexactly hurt(s|)\b"],
    "severity": [r"\bsever(ity|e)\b", r"\b(0|1|2|3|4|5|6|7|8|9|10)\b.*\bpain\b", r"\bpain scale\b"],
    "aggravators": [r"\bwhat makes.*worse\b", r"\bworse with\b", r"\baggravat"],
    "easers": [r"\bwhat helps\b", r"\bbetter with\b", r"\breliev"],
    "pattern": [r"\b24.?hour\b", r"\bmorning\b", r"\bat night\b", r"\bpattern\b"],
    "red_flags": [r"\bred flag", r"\bnumb|tingl", r"\bsaddle\b", r"\bfever\b", r"\bunexplained\b", r"\bweight loss\b"],
    "goals": [r"\bgoal", r"\bwhat do you want to get back to\b", r"\breturn to\b"],
    "work": [r"\bwork\b", r"\bjob\b", r"\bduty\b", r"\brestriction"],
    "transport": [r"\btransport\b", r"\bdrive\b", r"\bride(s|)\b", r"\bget here\b"],
    "summary": [r"\bsummar(y|ize)\b", r"\brecap\b", r"\blet me make sure\b"],
    "exam": [r"\btest\b", r"\bexam\b", r"\bpalpate\b", r"\brange\b", r"\barom\b", r"\border\b", r"\bdo.*(drawer|tilt|hawkins|neer|patell)"]
}

def detect_slots(user_text: str) -> List[str]:
    text = user_text.lower()
    hits = []
    for slot, patterns in SLOTS.items():
        for pat in patterns:
            if re.search(pat, text):
                hits.append(slot)
                break
    return hits

def wants_interpreter(user_text: str) -> bool:
    return bool(re.search(r"\b(interpreter|translate|translator)\b", user_text.lower()))

# --- Guardrails ---
DISALLOWED_ASKS = [
    r"\bwhat'?s my diagnosis\b",
    r"\bdiagnos(e|is)\b",
    r"\bcan you prescribe\b",
    r"\bwhat medication\b",
    r"\bimaging\b|\bx-?ray\b|\bMRI\b|\bCT\b"
]

def apply_guardrails(user_text: str, persona: Dict[str, Any]) -> str | None:
    txt = user_text.lower()
    for pat in DISALLOWED_ASKS:
        if re.search(pat, txt):
            return ("I'm not sure about that—I'm just here to tell you how it feels and what I notice day to day. "
                    "I don't know about diagnoses, imaging, or prescriptions.")
    return None

# --- Core reply ---
def patient_reply(user_text: str, persona: Dict[str, Any], state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], List[str]]:
    state = dict(state or {})
    tags: List[str] = []
    interp_needed = bool(persona["identity"].get("interpreter_needed")) and bool(persona["identity"].get("language"))
    language = persona["identity"].get("language")

    # Interpreter gate
    if interp_needed and not state.get("interpreter_provided", False):
        tags.append("interpreter_needed")
        if wants_interpreter(user_text):
            state["interpreter_provided"] = True
            return (f"Thank you. With an interpreter for {language}, I'm ready to continue. How can I help?", state, tags)
        else:
            return (f"Before we start, I need an interpreter for {language}, please.", state, tags)

    # Guardrails
    gr = apply_guardrails(user_text, persona)
    if gr:
        tags.append("guardrails_invoked")
        return (gr, state, tags)

    asked = detect_slots(user_text)
    tone = persona["communication_profile"].get("tone", "polite, concise")
    hpi = persona["hpi"]
    exam = persona["exam_script"]
    resp_parts = []

    # Map asked slots to content
    if "onset" in asked:
        resp_parts.append(f"It started {hpi.get('onset')}.")
        tags.append("asked_onset")
    if "mechanism" in asked:
        mech = hpi.get("mechanism") or "while being active"
        resp_parts.append(f"It happened {mech}.")
        tags.append("asked_mechanism")
    if "location" in asked:
        resp_parts.append("The pain is mostly in the " + (hpi.get("location") or "same area I described."))
        tags.append("asked_location")
    if "severity" in asked:
        sev = hpi.get("severity_nrs", 5)
        resp_parts.append(f"On a 0–10 scale it's about a {sev} right now.")
        tags.append("asked_severity")
    if "aggravators" in asked:
        resp_parts.append("It gets worse with " + ", ".join(hpi.get("aggravators", ["activity"])) + ".")
        tags.append("asked_aggravators")
    if "easers" in asked:
        resp_parts.append("It feels better with " + ", ".join(hpi.get("easers", ["rest"])) + ".")
        tags.append("asked_easers")
    if "pattern" in asked:
        resp_parts.append(f"Over 24 hours: {hpi.get('24h_pattern')}")
        tags.append("asked_24h_pattern")
    if "red_flags" in asked:
        rfs = hpi.get("red_flags") or []
        if rfs:
            resp_parts.append("I have noticed: " + ", ".join(rfs))
        else:
            resp_parts.append("I haven't noticed anything scary—no numbness, no tingling, no fever, nothing like that.")
        tags.append("screened_red_flags")
    if "goals" in asked:
        resp_parts.append("My goals are: " + "; ".join(persona.get("goals", [])))
        tags.append("asked_goals")
    if "work" in asked:
        ws = persona["context"].get("work_status") or "no restrictions"
        resp_parts.append(f"For work, I'm currently {ws}.")
        tags.append("asked_work_status")
    if "transport" in asked:
        tr = persona["sdoh"].get("transport") or "reliable"
        resp_parts.append(f"Getting to visits: my transportation is {tr}.")
        tags.append("asked_sdoH_transport")
    if "exam" in asked:
        # Summarize key exam nuggets
        obs = exam.get("observation")
        specials = exam.get("special_tests", {})
        specials_txt = "; ".join([f"{k}: {v}" for k, v in list(specials.items())[:3]]) if specials else "no special test findings reported"
        resp_parts.append(f"From the exam: {obs}. Special tests: {specials_txt}.")
        tags.append("asked_exam")

    if not resp_parts:
        # Default: gentle nudge depending on conversation phase
        if not state.get("shared_cc"):
            resp_parts.append(persona.get("chief_complaint") or "I've been having some pain that I'd like help with.")
            state["shared_cc"] = True
            tags.append("shared_cc")
        else:
            resp_parts.append("What would you like to know next? You can ask about when it started, how it happened, what makes it worse or better.")
    
    reply = " ".join(resp_parts)
    return reply, state, tags
