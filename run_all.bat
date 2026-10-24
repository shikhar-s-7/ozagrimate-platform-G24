@echo off
REM Starts the three FastAPI services in separate windows (Windows).
REM   Telemetry Ingestion Service   http://localhost:8081/docs
REM   Alert and Notification Service http://localhost:8082/docs
REM   Farm and Access Service       http://localhost:8083/docs
set ROOT=%~dp0
set PYTHONPATH=%ROOT%libs\ozagrimate_common;%PYTHONPATH%
start "telemetry-ingestion-service :8081" python -m uvicorn telemetry_ingestion.main:app --app-dir "%ROOT%services\telemetry-ingestion-service" --port 8081
start "alert-notification-service :8082" python -m uvicorn alert_notification.main:app --app-dir "%ROOT%services\alert-notification-service" --port 8082
start "farm-access-service :8083" python -m uvicorn farm_access.main:app --app-dir "%ROOT%services\farm-access-service" --port 8083
