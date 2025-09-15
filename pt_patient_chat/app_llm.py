
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List
from pathlib import Path
import csv

from engine import load_persona, patient_reply
from engine_llm import patient_reply_llm
from rubric import score_from_tags
from sse_starlette.sse import EventSourceResponse
from engine_llm import stream_patient_reply_llm
from starlette.staticfiles import StaticFiles
from llm_adapters import EchoLLMClient

# Try to initialize OpenAI if env flag & API key present; fall back to Echo client
USE_OPENAI = os.getenv("PT_USE_OPENAI", "").lower() in {"1","true","yes","on"}
CLIENT_NAME = "EchoLLMClient"
llm_client = EchoLLMClient()

if USE_OPENAI and os.getenv("OPENAI_API_KEY"):
    try:
        from llm_adapters import OpenAIChatClient
        llm_client = OpenAIChatClient()
        CLIENT_NAME = "OpenAIChatClient"
    except Exception as e:
        # Keep echo client, but record why
        CLIENT_NAME = f"EchoLLMClient (OpenAI init failed: {e})"

app = FastAPI(title="PT Sim Patient API (LLM-enabled)", version="0.4.0")

# Serve demo web UI
app.mount('/web', StaticFiles(directory=str(Path(__file__).resolve().parent / 'web'), html=True), name='web')

PERSONA_DIR = Path(__file__).resolve().parent / "personas"
MANIFEST = (Path(__file__).resolve().parent / "personas" / "MANIFEST.csv")

class ChatIn(BaseModel):
    patient_id: str
    user_text: str
    state: Dict[str, Any] | None = None

class ChatOut(BaseModel):
    reply: str
    state: Dict[str, Any]
    tags: List[str]

class ScoreIn(BaseModel):
    tags: List[str]

@app.get("/health")
def health():
    return {"status":"ok","llm_client": CLIENT_NAME}

@app.get("/patients")
def patients():
    items = []
    if MANIFEST.exists():
        with MANIFEST.open() as f:
            for row in csv.DictReader(f):
                items.append(row)
    else:
        for p in PERSONA_DIR.glob("P-*.persona.json"):
            items.append({"patient_id": p.stem.replace(".persona","")})
    return {"patients": items}

@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    persona = load_persona(body.patient_id)  # probe existence
    reply, state, tags = patient_reply(body.user_text, persona, body.state or {})
    return {"reply": reply, "state": state, "tags": tags}

@app.post("/chat_llm", response_model=ChatOut)
def chat_llm(body: ChatIn):
    reply, state, tags = patient_reply_llm(body.user_text, body.patient_id, body.state or {}, llm=llm_client)
    return {"reply": reply, "state": state, "tags": tags}

@app.post("/score")
def score(body: ScoreIn):
    return score_from_tags(body.tags)


@app.post("/chat_llm_stream")
def chat_llm_stream(body: ChatIn):
    def event_gen():
        # Stream tokens
        for kind, payload in stream_patient_reply_llm(body.user_text, body.patient_id, body.state or {}, llm=llm_client):
            if kind == "token":
                yield {"event": "token", "data": payload}
            elif kind == "meta":
                yield {"event": "meta", "data": json.dumps(payload)}
        yield {"event": "done", "data": ""}
    return EventSourceResponse(event_gen())
