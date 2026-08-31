"""
Mongo access layer.

In production (Render), set MONGODB_URI to your MongoDB Atlas connection
string and everything talks to the real database.

For local development, if MONGODB_URI is empty or unreachable, this
automatically falls back to `mongomock` — an in-memory Mongo-compatible
database — so `python app.py` works immediately without needing an
Atlas account. Data in mongomock mode does NOT persist between restarts.

IMPORTANT: the client is created ONCE per Flask app (cached on
app.extensions) and reused for every request. It deliberately does NOT
live in Flask's per-request `g`, because a fresh mongomock.MongoClient()
is a brand new empty in-memory database — caching only in `g` would wipe
"seeded" data on literally every single request.
"""
import os
import sys
from flask import current_app, g


def _is_production_environment():
    return bool(
        os.environ.get("VERCEL")
        or os.environ.get("FLASK_ENV") == "production"
        or os.environ.get("ENV") == "production"
    )


def _get_or_create_client(app):
    if "mongo_client" in app.extensions:
        client = app.extensions["mongo_client"]
        backend = app.extensions["mongo_backend"]
        return client, backend

    uri = app.config.get("MONGODB_URI")
    db_name = app.config.get("MONGODB_DB", "techfinix26")

    if uri:
        try:
            from pymongo import MongoClient
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000,
            )
            client.admin.command("ping")
            app.extensions["mongo_client"] = client
            app.extensions["mongo_backend"] = "atlas"
            app.logger.info(f"[mongodb] Successfully connected to MongoDB Atlas, db='{db_name}'.")
            return client, "atlas"
        except Exception as exc:  # noqa: BLE001
            app.logger.error(f"[mongodb] CRITICAL: Failed to connect to MongoDB Atlas: {exc}")
            if _is_production_environment():
                raise RuntimeError(
                    f"MongoDB Atlas connection failed in production environment: {exc}. "
                    f"Please check MONGODB_URI in Vercel project environment settings and verify "
                    f"that MongoDB Atlas Network Access includes 0.0.0.0/0."
                ) from exc
            print(
                f"[mongodb] Could not reach MONGODB_URI ({exc}); falling back to in-memory mongomock for local dev.",
                file=sys.stderr,
            )

    if _is_production_environment():
        app.logger.error("[mongodb] CRITICAL: MONGODB_URI environment variable is missing in production deployment!")
        raise RuntimeError(
            "MONGODB_URI environment variable is not configured in Vercel environment settings. "
            "Please add MONGODB_URI under Project Settings -> Environment Variables in Vercel."
        )

    try:
        import mongomock
    except ImportError:
        raise RuntimeError(
            "MONGODB_URI is not set or unreachable, and mongomock is not installed. "
            "Either check your MongoDB Atlas IP Whitelist / MONGODB_URI in .env, or run "
            "`pip install mongomock` for local development."
        )
    client = mongomock.MongoClient()
    app.extensions["mongo_client"] = client
    app.extensions["mongo_backend"] = "mongomock"
    app.logger.warning(
        "[mongodb] MONGODB_URI not set or unreachable — using in-memory mongomock for local dev."
    )
    return client, "mongomock"


def get_db():
    if "db" not in g:
        app = current_app._get_current_object()
        client, backend = _get_or_create_client(app)
        g.db = client[app.config.get("MONGODB_DB")]
        g._db_backend = backend
    return g.db


def ensure_indexes(db):
    db.users.create_index("username", unique=True, sparse=True)
    db.users.create_index("participant_id", unique=True, sparse=True)
    db.events.create_index("slug", unique=True)
    db.photos.create_index("event_slug")
    db.results.create_index("event_slug", unique=True)
