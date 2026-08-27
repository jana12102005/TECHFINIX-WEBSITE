"""
Bulk-imports participants from a CSV or Excel file and creates their
login accounts with auto-generated temporary passwords.

Input file must have these columns (any order):
    Participant ID | Name | Email | Event | Team

Event values should match an event 'slug' from seed_events.py
(e.g. "molecule-docking"), or the event NAME — both are accepted.

Usage:
    python database/import_participants.py participants.xlsx
    python database/import_participants.py participants.csv

Output:
    TECHFINIX26_Login_Credentials.xlsx — hand this to your participants.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database._connection import get_client  # noqa: E402
from app.services.security import hash_password, generate_temp_password  # noqa: E402

import pandas as pd  # noqa: E402


COLUMN_ALIASES = {
    "participant id": "participant_id",
    "participant_id": "participant_id",
    "name": "name",
    "email": "email",
    "event": "event",
    "team": "team",
}


def normalize_columns(df):
    df = df.rename(columns={c: COLUMN_ALIASES.get(c.strip().lower(), c) for c in df.columns})
    required = {"participant_id", "name", "event"}
    missing = required - set(df.columns)
    if missing:
        sys.exit(f"Input file is missing required column(s): {', '.join(sorted(missing))}")
    return df


def resolve_event_slug(db, value):
    value = str(value).strip()
    by_slug = db.events.find_one({"slug": value})
    if by_slug:
        return by_slug["slug"]
    by_name = db.events.find_one({"name": {"$regex": f"^{value}$", "$options": "i"}})
    if by_name:
        return by_name["slug"]
    return value.lower().replace(" ", "-")  # best-effort fallback


def run():
    if len(sys.argv) < 2:
        sys.exit("Usage: python database/import_participants.py <participants.xlsx|.csv>")

    path = sys.argv[1]
    if not os.path.exists(path):
        sys.exit(f"File not found: {path}")

    df = pd.read_csv(path) if path.lower().endswith(".csv") else pd.read_excel(path)
    df = normalize_columns(df)

    client = get_client()
    db = client[os.environ.get("MONGODB_DB", "techfinix26")]

    credential_rows = []
    created, skipped = 0, 0

    for _, row in df.iterrows():
        pid = str(row["participant_id"]).strip().upper()
        if not pid or pid.lower() == "nan":
            continue

        existing = db.users.find_one({"participant_id": pid})
        if existing:
            skipped += 1
            continue

        temp_password = generate_temp_password()
        event_slug = resolve_event_slug(db, row.get("event", ""))

        db.users.insert_one({
            "participant_id": pid,
            "name": str(row.get("name", "")).strip(),
            "email": str(row.get("email", "")).strip() if pd.notna(row.get("email")) else "",
            "event": event_slug,
            "team": str(row.get("team", "")).strip() if pd.notna(row.get("team")) else "",
            "role": "participant",
            "password_hash": hash_password(temp_password),
        })

        credential_rows.append({
            "Participant ID": pid,
            "Name": row.get("name", ""),
            "Username": pid,
            "Temporary Password": temp_password,
            "Event": event_slug,
        })
        created += 1

    out_path = "TECHFINIX26_Login_Credentials.xlsx"
    if credential_rows:
        pd.DataFrame(credential_rows).to_excel(out_path, index=False)

    print(f"Created {created} participant account(s). Skipped {skipped} that already existed.")
    if credential_rows:
        print(f"Credentials written to: {out_path}")
        print("Distribute this file to participants, then delete your local copy.")


if __name__ == "__main__":
    run()
