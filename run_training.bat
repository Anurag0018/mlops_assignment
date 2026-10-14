@echo off
echo ============================================================
echo Running Student Performance MLOps Training Pipeline
echo 1. Building Features
echo 2. Benchmarking Models (Logistic Regression, RF, XGBoost)
echo 3. Logging Runs & Artifacts to MLflow
echo 4. Registering Champion Model
echo ============================================================
python src/features/build_features.py
python src/training/train.py
pause
