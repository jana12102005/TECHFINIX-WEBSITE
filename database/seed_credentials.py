"""
Seeds BOTH coordinator and participant login credentials directly from
the lists below — no Excel/CSV file needed. Good for a quick demo, or
as a starting template: edit the lists with your real people and run it.

(If you already have a spreadsheet of participants, you can use
`database/import_participants.py` instead for the participant side —
it does the same thing but reads from a file. Coordinators are edited
here or in `database/create_coordinators.py`, whichever you prefer.)

Coordinator passwords are set explicitly below (you choose them).
Participant passwords are auto-generated (never stored in plain text —
both are hashed with Werkzeug/PBKDF2 before saving to MongoDB).

Run:
    python database/seed_credentials.py

Output:
    TECHFINIX26_Login_Credentials.xlsx — one file with two sheets,
    "Coordinators" and "Participants". Distribute the relevant rows,
    then delete your local copy.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database._connection import get_client  # noqa: E402
from app.services.security import hash_password, generate_temp_password  # noqa: E402

import pandas as pd  # noqa: E402


# ---- Coordinators -----------------------------------------------------
# role: "super_coordinator" (manages every event) or "event_coordinator"
# (only the events listed in assigned_events — slugs must match
# database/seed_events.py: project-expo | paper-presentation |
# experiment-detection | molecule-docking | biomolecule-puzzle)
COORDINATORS = [
    {"username": "admin", "name": "Super Coordinator", "password": "TECHFINIX26-ADMIN",
     "role": "super_coordinator", "assigned_events": []},
    {"username": "biotech_coord", "name": "Event Coordinator", "password": "TECHFINIX26-COORD",
     "role": "event_coordinator", "assigned_events": ["experiment-detection", "biomolecule-puzzle"]},
]

# ---- Participants -------------------------------------------------------
# 'event' must match a slug from database/seed_events.py (see list above).
PARTICIPANTS = [
    {"participant_id": "TF26-001", "name": "Student 1", "email": "student1@email.com",
     "event": "molecule-docking", "team": "BioForce"},
    {"participant_id": "TF26-002", "name": "Student 2", "email": "student2@email.com",
     "event": "project-expo", "team": "BioInnovators"},
    {"participant_id": "TF26-003", "name": "Student 3", "email": "student3@email.com",
     "event": "biomolecule-puzzle", "team": "BioSquad"},
]


def seed_coordinators(db):
    rows, created, updated = [], 0, 0

    for c in COORDINATORS:
        username = c["username"].strip().lower()
        exists = db.users.find_one({"username": username})

        db.users.update_one(
            {"username": username},
            {"$set": {
                "username": username,
                "password_hash": hash_password(c["password"]),
                "name": c.get("name", username),
                "role": c["role"],
                "assigned_events": c.get("assigned_events", []),
            }},
            upsert=True,
        )

        rows.append({
            "Username": username,
            "Name": c.get("name", ""),
            "Password": c["password"],
            "Role": c["role"],
            "Assigned Events": ", ".join(c.get("assigned_events", [])) or "ALL",
        })
        if exists:
            updated += 1
            print(f"  ↻ coordinator updated: {username} ({c['role']})")
        else:
            created += 1
            print(f"  ✓ coordinator created: {username} ({c['role']})")

    print(f"Coordinators: {created} created, {updated} updated.\n")
    return rows


def seed_participants(db):
    rows, created, skipped = [], 0, 0

    for p in PARTICIPANTS:
        pid = p["participant_id"].strip().upper()

        if db.users.find_one({"participant_id": pid}):
            print(f"  – participant already exists, skipping: {pid}")
            skipped += 1
            continue

        temp_password = generate_temp_password()

        db.users.insert_one({
            "participant_id": pid,
            "name": p.get("name", ""),
            "email": p.get("email", ""),
            "event": p.get("event", ""),
            "team": p.get("team", ""),
            "role": "participant",
            "password_hash": hash_password(temp_password),
        })

        rows.append({
            "Participant ID": pid,
            "Name": p.get("name", ""),
            "Username": pid,
            "Temporary Password": temp_password,
            "Event": p.get("event", ""),
        })
        created += 1
        print(f"  ✓ participant created: {pid} — {temp_password}")

    print(f"Participants: {created} created, {skipped} skipped (already existed).\n")
    return rows


def run():
    client = get_client()
    db = client[os.environ.get("MONGODB_DB", "techfinix26")]

    print("Seeding coordinators...")
    coordinator_rows = seed_coordinators(db)

    print("Seeding participants...")
    participant_rows = seed_participants(db)

    out_path = "TECHFINIX26_Login_Credentials.xlsx"
    if coordinator_rows or participant_rows:
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            if coordinator_rows:
                pd.DataFrame(coordinator_rows).to_excel(writer, sheet_name="Coordinators", index=False)
            if participant_rows:
                pd.DataFrame(participant_rows).to_excel(writer, sheet_name="Participants", index=False)
        print(f"Credentials written to: {out_path} (sheets: Coordinators, Participants)")
        print("Distribute the relevant rows to each person, then delete your local copy.")
    else:
        print("Nothing new to write — everyone in the lists already exists.")


if __name__ == "__main__":
    run()