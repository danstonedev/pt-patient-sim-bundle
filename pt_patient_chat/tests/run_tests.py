
# Lightweight tests: run with `python tests/run_tests.py`
import os, sys, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from prompt_builder import build_messages
from engine_llm import patient_reply_llm, apply_guardrails
from llm_adapters import EchoLLMClient

PERSONA_ID_SIMPLE = "P-0002"  # ankle sprain persona
PERSONA_ID_INTERP = "P-0011"  # interpreter-needed persona (Ukrainian)

def test_prompt_builder():
    # Load a persona
    ppath = ROOT / "personas_sport_ortho_v1" / f"{PERSONA_ID_SIMPLE}.persona.json"
    assert ppath.exists(), f"Missing persona file: {ppath}"
    persona = json.loads(ppath.read_text())
    msgs = build_messages(persona, "When did this start?", state={})
    assert isinstance(msgs, list) and len(msgs) >= 3, "Prompt should have system+context+user"
    roles = [m["role"] for m in msgs]
    assert roles.count("system") >= 2 and roles.count("user") >= 1, f"Unexpected roles: {roles}"
    assert any("PERSONA CONTEXT" in m["content"] for m in msgs if m["role"]=="system"), "Missing persona context"

def test_guardrails():
    txt = "What's my diagnosis and should I get an MRI?"
    out = apply_guardrails(txt)
    assert isinstance(out, str) and "diagnosis" in out.lower(), "Guardrails should trigger on diagnosis/imaging asks"

def test_patient_reply_llm_echo():
    # Use echo client to stay offline
    client = EchoLLMClient()
    reply, state, tags = patient_reply_llm("When did this start and how did it happen?", PERSONA_ID_SIMPLE, {}, llm=client)
    assert isinstance(reply, str) and reply, "LLM reply should be a non-empty string"
    assert "asked_onset" in tags and "asked_mechanism" in tags, f"Tags missing expected items: {tags}"
    assert state.get("shared_cc") is True, "State should mark shared_cc after first turn"

def test_interpreter_gate():
    client = EchoLLMClient()
    reply, state, tags = patient_reply_llm("hi", PERSONA_ID_INTERP, {}, llm=client)
    assert "interpreter" in reply.lower(), "Interpreter-needed personas should ask for interpreter first"
    assert "interpreter_needed" in tags, "Tag should include interpreter_needed"

if __name__ == "__main__":
    ok = 0; total = 4
    try:
        test_prompt_builder(); ok += 1; print("✅ test_prompt_builder")
    except AssertionError as e:
        print("❌ test_prompt_builder:", e)
    try:
        test_guardrails(); ok += 1; print("✅ test_guardrails")
    except AssertionError as e:
        print("❌ test_guardrails:", e)
    try:
        test_patient_reply_llm_echo(); ok += 1; print("✅ test_patient_reply_llm_echo")
    except AssertionError as e:
        print("❌ test_patient_reply_llm_echo:", e)
    try:
        test_interpreter_gate(); ok += 1; print("✅ test_interpreter_gate")
    except AssertionError as e:
        print("❌ test_interpreter_gate:", e)
    print(f"\nPassed {ok}/{total} tests")
