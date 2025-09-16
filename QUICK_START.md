# 🏥 PT Patient Simulator - Quick Start Guide

## ✅ **Current Status: Ready to Use!**

Your PT Patient Simulation app is configured and running with:
- **Backend**: OpenAI API (GPT-4o-mini)
- **Status**: ✅ Connected and working
- **Server**: Running at http://127.0.0.1:8001

## 🚀 **How to Start**

1. **Start the server**:
   ```bash
   python pt_patient_chat\app.py
   ```

2. **Open in browser**: http://127.0.0.1:8001/web/simple_chat.html

3. **Select a patient** from the dropdown and start chatting!

## 🎭 **Available Patients**

Your app includes 15 different patient personas with various medical conditions and communication styles:
- P-0001: Various orthopedic and neurological cases
- P-0002 through P-0015: Diverse medical scenarios

## 🔧 **Configuration**

- **Config file**: `pt_patient_chat\.env` 
- **Current backend**: OpenAI API only (other backends hidden for simplicity)
- **API Key**: Configured and working ✅

## 🧪 **Testing**

To test the connection:
```bash
python test_llm_connections.py
```

## 📝 **Features**

- ✅ Real-time chat with AI patients
- ✅ Patient persona switching
- ✅ Production-ready logging
- ✅ Clean, modern web interface
- ✅ Multi-backend architecture (extensible for future)

## 🎯 **Next Steps**

- The app is ready for use with OpenAI
- Other LLM backends (Ollama, local LLMs) are available but hidden for simplicity
- When you're ready to explore other backends, use `switch_llm.bat`

---
**Server URL**: http://127.0.0.1:8001/web/simple_chat.html