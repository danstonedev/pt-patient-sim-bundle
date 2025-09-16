# PT Patient Simulator

A simplified patient simulation system for physical therapy education, allowing PT students to practice interactions with patients displaying different pain behaviors.

## Overview

This system simulates patient conversations with **12 distinct behavioral combinations** (2×3×2):
- **Cooperation**: Willing, Resistant
- **Pain Expression**: Stoic, Normal, Dramatic  
- **Talkativeness**: Normal, Verbose

The system prioritizes **pain expression** as the dominant behavioral trait, ensuring authentic patient responses.

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r pt_patient_chat/requirements.txt
   ```

2. **Set OpenAI API Key**
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY='your-api-key-here'
   $env:PT_USE_OPENAI='1'
   $env:OPENAI_MODEL='gpt-4o-mini'
   ```

3. **Start Server**
   ```bash
   cd pt_patient_chat
   python app_simple.py
   ```

4. **Open Interface**
   Navigate to: `http://localhost:8002/web/behavior_test_simple.html`

## Features

### Comparison Testing Interface
- **Patient Selection**: Choose from 15 available patient personas
- **12-Combination Grid**: Compare all behavioral combinations simultaneously
- **Real-time AI Responses**: Each combination generates authentic patient responses
- **Educational Focus**: Clean interface designed for PT student learning

### Patient Behaviors

#### Pain Expression (Priority Behavior)
- **Stoic**: Philosophical acceptance, minimal emotional expression
- **Normal**: Balanced emotional response to pain
- **Dramatic**: Heightened emotional expression and concern

#### Cooperation Levels
- **Willing**: Engaged, follows instructions, asks clarifying questions
- **Resistant**: Hesitant, questions necessity, may avoid activities

#### Talkativeness
- **Normal**: Standard conversational responses
- **Verbose**: Detailed explanations, additional context, longer responses

## File Structure

```
pt-patient-sim-bundle/
├── README.md                           # This file
├── pt_patient_chat/                    # Main application directory
│   ├── app_simple.py                   # Server with 12-combination system
│   ├── llm_adapters.py                 # AI integration utilities
│   ├── requirements.txt                # Python dependencies
│   ├── config.example.env              # Environment configuration template
│   ├── personas/                       # Patient persona files (15 patients)
│   │   ├── MANIFEST.csv
│   │   └── P-*.persona.json
│   └── web/                           # Web interface
│       ├── behavior_test_simple.html   # Main comparison interface
│       └── favicon.ico
```

## System Architecture

- **Backend**: FastAPI server with OpenAI GPT-4o-mini integration
- **Frontend**: Clean HTML/JavaScript interface for behavior comparison
- **AI Prompting**: Prioritized system prompts ensure pain expression dominance
- **Patient Data**: JSON-based persona system with medical histories

## Educational Use

This tool is designed for PT education to help students:
- Recognize different pain expression patterns
- Practice communication with various cooperation levels
- Understand how patient personality affects treatment interactions
- Compare behavioral responses side-by-side for learning

## Configuration

Environment variables in `pt_patient_chat/.env`:
- `PT_USE_OPENAI=1` - Enable OpenAI integration
- `OPENAI_API_KEY` - Your OpenAI API key
- `OPENAI_MODEL=gpt-4o-mini` - AI model to use