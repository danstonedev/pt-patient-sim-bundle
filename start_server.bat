@echo off
echo Starting PT Patient Simulator...
echo.

REM Navigate to the correct directory
cd /d "C:\Users\danst\OneDrive\Desktop\pt_patient_sim_bundle_v3\pt-patient-sim-bundle\pt_patient_chat"

REM Set environment variables
set PT_USE_OPENAI=1
set OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE
set OPENAI_MODEL=gpt-4o-mini
set PORT=8002

echo Environment set:
echo - Directory: %CD%
echo - OpenAI: %PT_USE_OPENAI%
echo - Model: %OPENAI_MODEL%
echo - Port: %PORT%
echo.

echo Starting server...
python app_simple.py

pause