@echo off
echo Starting PT Patient Simulator...
echo.
echo Make sure you have set your OpenAI API key:
echo $env:OPENAI_API_KEY='your-api-key-here'
echo $env:PT_USE_OPENAI='1' 
echo $env:OPENAI_MODEL='gpt-4o-mini'
echo.
echo Starting server on port 8002...
cd pt_patient_chat
python app_simple.py
pause