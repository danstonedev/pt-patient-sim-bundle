
# PT Patient Simulation Chatbot

A simple, clean LLM-powered chatbot that simulates patient interactions for physical therapy training.

## Features

- **15 Realistic Patient Personas**: Each with unique medical conditions, communication styles, and backgrounds
- **OpenAI Integration**: Uses GPT-4o-mini for natural, contextual responses
- **Role-Playing AI**: LLM stays in character as the selected patient
- **Clean Web Interface**: Simple, modern chat interface
- **No Complexity**: No scoring, minimal setup, just functional chatbot

## Quick Start

1. **Install Dependencies**:
   ```powershell
   .venv\Scripts\python.exe -m pip install -r pt_patient_chat/requirements.txt
   ```

2. **Configure OpenAI** (create `.env` file or set environment variables):
   ```
   PT_USE_OPENAI=1
   OPENAI_API_KEY=your-openai-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   ```

3. **Start the Server**:
   ```powershell
   $env:PT_USE_OPENAI='1'
   $env:OPENAI_API_KEY='your-key-here' 
   $env:OPENAI_MODEL='gpt-4o-mini'
   .venv\Scripts\python.exe pt_patient_chat\app.py
   ```

4. **Open the Web Interface**:
   Visit: http://127.0.0.1:8001/web/simple_chat.html

## How to Use

1. **Select a Patient**: Choose from the dropdown (e.g., "Jack - Hip contusion")
2. **Start Chatting**: The AI will respond as that patient based on their persona
3. **Natural Conversations**: Ask about symptoms, pain, daily activities, etc.

## Example Patients

- **Jack (P-0001)**: 69-year-old with hip pain from ice fall, polite and concise
- **Various Others**: Different ages, conditions, communication styles, and backgrounds

## File Structure

```
pt_patient_chat/
├── app.py                 # Main FastAPI application
├── llm_adapters.py        # OpenAI and Echo LLM clients
├── personas/              # Patient persona JSON files
├── web/
│   └── simple_chat.html   # Web interface
├── requirements.txt       # Python dependencies
└── .env                   # Configuration (create this)
```

## API Endpoints

- `GET /health` - Server status and LLM client info
- `GET /patients` - List all available patients
- `GET /patients/{id}` - Get specific patient details  
- `POST /chat` - Send message and get patient response

## Patient Personas

Each patient has:
- **Identity**: Name, age, pronouns, language
- **Medical**: Condition, symptoms, pain levels
- **Communication**: Tone, talkativeness, health literacy
- **Background**: Location, occupation, lifestyle

The LLM uses this data to respond authentically as that patient would.

## Development

To run without OpenAI (for testing):
```powershell
$env:PT_USE_OPENAI='0'
.venv\Scripts\python.exe pt_patient_chat\app.py
```

This uses an "Echo" client that just repeats your messages for testing the interface.
