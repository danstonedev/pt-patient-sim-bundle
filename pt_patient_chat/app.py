
# Minimal FastAPI app exposing /patients, /chat, /score
# Usage (in your environment): pip install fastapi uvicorn
# uvicorn app:app --reload
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List
from pathlib import Path
import csv, json

from engine import load_persona, patient_reply
from rubric import score_from_tags

app = FastAPI(title="PT Sim Patient API", version="0.1.0")

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

@app.get("/patients")
def patients():
    items = []
    if MANIFEST.exists():
        with MANIFEST.open() as f:
            for row in csv.DictReader(f):
                items.append(row)
    else:
        # fallback: list persona files
        for p in PERSONA_DIR.glob("P-*.persona.json"):
            items.append({"patient_id": p.stem.replace(".persona","")})
    return {"patients": items}

@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    persona = load_persona(body.patient_id)
    reply, state, tags = patient_reply(body.user_text, persona, body.state or {})
    return {"reply": reply, "state": state, "tags": tags}

@app.post("/score")
def score(body: ScoreIn):
    return score_from_tags(body.tags)
