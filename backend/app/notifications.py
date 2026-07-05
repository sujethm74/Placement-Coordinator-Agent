"""
Notification System (simulated).

In a real deployment this would push to an email/SMS provider or a
websocket. For this project it:
  1. Prints to the server console (simulating an email send), and
  2. Appends to an in-memory list so the frontend can poll /notifications
     and show a live alert feed (e.g. upcoming deadlines, interviews,
     status changes).
"""
from datetime import datetime
from typing import List, Dict

_NOTIFICATIONS: List[Dict] = []
_MAX_STORED = 200


def notify(message: str, category: str = "info"):
    entry = {
        "message": message,
        "category": category,
        "timestamp": datetime.utcnow().isoformat(),
    }
    print(f"[MOCK EMAIL/NOTIFICATION] {entry['timestamp']} — {message}")
    _NOTIFICATIONS.insert(0, entry)
    del _NOTIFICATIONS[_MAX_STORED:]


def get_notifications(limit: int = 50) -> List[Dict]:
    return _NOTIFICATIONS[:limit]
