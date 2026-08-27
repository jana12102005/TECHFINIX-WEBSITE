"""
Shared connection helper for the standalone database/ scripts
(setup_database.py, seed_events.py, create_coordinators.py, import_participants.py).

These scripts talk to a *real* MongoDB (Atlas or local mongod) — they
intentionally do NOT fall back to mongomock, since their whole purpose
is to write data that the deployed app should actually see.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()


def get_client():
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        print(
            "ERROR: MONGODB_URI is not set.\n"
            "Set it in your .env file (or as a real environment variable) "
            "to your MongoDB Atlas connection string before running "
            "scripts in database/.",
            file=sys.stderr,
        )
        sys.exit(1)
    from pymongo import MongoClient
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")  # fail fast with a clear error if unreachable
    return client
