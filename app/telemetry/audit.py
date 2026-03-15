# app/telemetry/audit.py
import json
import time

def audit_log(event: dict):
    event["ts"] = time.time()
    print(json.dumps(event, ensure_ascii=False))
