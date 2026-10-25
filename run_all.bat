@echo off
REM Starts the three FastAPI services, each in its own window (Windows).
REM Run it from a terminal where the virtual environment is activated.
REM Each window stays open, so a start-up error stays visible; close a window to stop that service.
REM   Telemetry Ingestion Service    http://localhost:8081/docs
REM   Alert and Notification Service http://localhost:8082/docs
REM   Farm and Access Service        http://localhost:8083/docs
set ROOT=%~dp0
set PYTHONPATH=%ROOT%libs\ozagrimate_common;%PYTHONPATH%
start "telemetry-ingestion-service :8081" cmd /k python -m uvicorn telemetry_ingestion.main:app --app-dir "%ROOT%services\telemetry-ingestion-service" --port 8081
start "alert-notification-service :8082" cmd /k python -m uvicorn alert_notification.main:app --app-dir "%ROOT%services\alert-notification-service" --port 8082
start "farm-access-service :8083" cmd /k python -m uvicorn farm_access.main:app --app-dir "%ROOT%services\farm-access-service" --port 8083
