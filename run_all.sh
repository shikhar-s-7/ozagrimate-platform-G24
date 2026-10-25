#!/usr/bin/env bash
# Starts the three FastAPI services, each on its own port. Ctrl+C stops all three.
#   Telemetry Ingestion Service   http://localhost:8081/docs
#   Alert & Notification Service  http://localhost:8082/docs
#   Farm & Access Service         http://localhost:8083/docs
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"
# The shared library is also installed by requirements.txt; this keeps the services
# starting even if that editable install is not picked up.
export PYTHONPATH="$ROOT/libs/ozagrimate_common${PYTHONPATH:+:$PYTHONPATH}"
trap 'kill 0' EXIT

"$PY" -m uvicorn telemetry_ingestion.main:app --app-dir "$ROOT/services/telemetry-ingestion-service" --port 8081 &
"$PY" -m uvicorn alert_notification.main:app --app-dir "$ROOT/services/alert-notification-service" --port 8082 &
"$PY" -m uvicorn farm_access.main:app --app-dir "$ROOT/services/farm-access-service" --port 8083 &
wait
