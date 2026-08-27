"""
Creates/updates coordinator accounts.

Edit the COORDINATORS list below, then run:
    python database/create_coordinators.py

A "super_coordinator" can manage every event and publish any result.
An "event_coordinator" can only manage the events listed in
assigned_events (must match an event 'slug' from seed_events.py).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database._connection import get_client  # noqa: E402
from app.services.security import hash_password  # noqa: E402

COORDINATORS = [
    {
        "username": "admin",
        "password": "CHANGE_ME_BEFORE_LAUNCH",
        "name": "Super Coordinator",
        "role": "super_coordinator",
        "assigned_events": [],
    },
    {
        "username": "biotech_coord",
        "password": "CHANGE_ME_BEFORE_LAUNCH",
        "name": "Event Coordinator",
        "role": "event_coordinator",
        "assigned_events": ["experiment-detection", "biomolecule-puzzle"],
    },
]


def run():
    client = get_client()
    db = client[os.environ.get("MONGODB_DB", "techfinix26")]

    for c in COORDINATORS:
        db.users.update_one(
            {"username": c["username"]},
            {"$set": {
                "username": c["username"],
                "password_hash": hash_password(c["password"]),
                "name": c["name"],
                "role": c["role"],
                "assigned_events": c["assigned_events"],
            }},
            upsert=True,
        )
        print(f"  ✓ {c['role']}: {c['username']}")

    print(f"\n{len(COORDINATORS)} coordinator account(s) created/updated.")
    print("IMPORTANT: change the placeholder passwords above before going live.")


if __name__ == "__main__":
    run()
