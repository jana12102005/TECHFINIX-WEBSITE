"""
Connects to MongoDB Atlas and creates the indexes TECHFINIX '26 needs.
MongoDB creates collections lazily, so this mainly exists to set up
indexes and confirm the connection works before you run the other
database/ scripts.

Run:
    python database/setup_database.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database._connection import get_client  # noqa: E402


def run():
    client = get_client()
    db = client[os.environ.get("MONGODB_DB", "techfinix26")]

    db.users.create_index("username", unique=True, sparse=True)
    db.users.create_index("participant_id", unique=True, sparse=True)
    db.events.create_index("slug", unique=True)
    db.photos.create_index("event_slug")
    db.results.create_index("event_slug", unique=True)

    print(f"Connected to database: {db.name}")
    print("Indexes created:")
    print("  users.username (unique, sparse)")
    print("  users.participant_id (unique, sparse)")
    print("  events.slug (unique)")
    print("  photos.event_slug")
    print("  results.event_slug (unique)")
    print("\nNext steps:")
    print("  python database/seed_events.py")
    print("  python database/create_coordinators.py")
    print("  python database/import_participants.py participants.xlsx")


if __name__ == "__main__":
    run()
