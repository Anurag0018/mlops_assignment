@echo off
echo ============================================================
echo Starting Student Risk Prediction FastAPI Microservice
echo Service: http://localhost:8000
echo Swagger Docs: http://localhost:8000/docs
echo ============================================================
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
pause
