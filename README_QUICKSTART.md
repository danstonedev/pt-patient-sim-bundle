
# PT Simulated Patient — Quickstart

## 1) Open in VS Code
- Unzip the bundle and open the folder in VS Code.

## 2) Create and activate a virtual environment (recommended)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

## 3) Install dependencies
```bash
pip install -r pt_patient_chat/requirements.txt
```

## 4) (Optional) enable OpenAI client
```bash
cp pt_patient_chat/config.example.env pt_patient_chat/.env
# edit pt_patient_chat/.env and set OPENAI_API_KEY, and optionally set PT_USE_OPENAI=1
```

## 5) Run the API (from VS Code or terminal)
- VS Code: Run configuration **Uvicorn: app_llm** (F5)
- Terminal:
```bash
uvicorn pt_patient_chat.app_llm:app --reload
```

## 6) Try the endpoints
```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/patients
curl -s -X POST http://127.0.0.1:8000/chat_llm -H "Content-Type: application/json"   -d '{"patient_id":"P-0002","user_text":"When did this start and how did it happen?","state":{}}'
```

## 7) Run tests
```bash
python pt_patient_chat/tests/run_tests.py
```
