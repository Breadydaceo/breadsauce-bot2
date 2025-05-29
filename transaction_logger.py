
import json
import os
from datetime import datetime

LOG_FILE = "transaction_log.json"

def log_transaction(event_type, user_id, username, details):
    timestamp = datetime.utcnow().isoformat()
    entry = {
        "timestamp": timestamp,
        "type": event_type,
        "user_id": user_id,
        "username": username,
        "details": details
    }

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([entry], f, indent=2)
    else:
        with open(LOG_FILE, "r+") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)
