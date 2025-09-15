
# PT Simulated Patient Chat (Reference Harness)

This mini-project turns your persona JSONs into a talking patient for training.

## What you have
- `engine.py` – core logic: loads persona, detects what the learner asked, applies guardrails, and replies in-patient voice.
- `rubric.py` – lightweight scoring by conversation tags (onset, mechanism, red flags, etc.).
- `app.py` – FastAPI microservice exposing `/patients`, `/chat`, `/score`.
- `run_cli.py` – command-line tester.
- Personas source: `/mnt/data/personas_sport_ortho_v1`

## Quick start (CLI)
```bash
python run_cli.py P-0002
# Tip: if the persona needs an interpreter, say: "An interpreter is present now."
```

## API start (if FastAPI is available)
```bash
pip install fastapi uvicorn pydantic
uvicorn app:app --reload
```
Then:
```bash
curl -s http://127.0.0.1:8000/patients
curl -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json"   -d '{"patient_id":"P-0002","user_text":"When did this start and how did it happen?","state":{}}'
```

## Integration notes
- The engine enforces interpreter flow, declines diagnosis/prescriptions/imaging, and only reveals exam nuggets when asked.
- Returned `tags` can be accumulated client-side and passed to `/score` at the end to produce a rubric grade.
- You can swap personas simply by passing a different `patient_id` tied to your JSONs.
- To use a real LLM instead of rule-based replies, replace `patient_reply` with a prompt-builder that feeds the persona + guardrails to your model, but **keep** the tag extraction for scoring.

## License
For instructional/simulation use. Synthetic data only.


## Use OpenAI by default (env flag)
Set `PT_USE_OPENAI=1` and `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`) before launching the API:
```bash
export PT_USE_OPENAI=1
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini
uvicorn /mnt/data/pt_patient_chat/app_llm:app --reload
# Check which client is active
curl -s http://127.0.0.1:8000/health
```

## Run tests
```bash
python /mnt/data/pt_patient_chat/tests/run_tests.py
```


**Note:** Personas are now bundled under `pt_patient_chat/personas/` and all paths are relative.
