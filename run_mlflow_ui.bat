@echo off
echo ============================================================
echo Starting MLflow Experiment Tracking UI
echo Access Dashboard at: http://localhost:5000
echo Tracking Store: sqlite:///mlruns.db
echo ============================================================
mlflow ui --backend-store-uri sqlite:///mlruns.db --port 5000
pause
