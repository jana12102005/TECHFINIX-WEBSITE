from flask import Flask

from .config import Config
from .services.mongodb import get_db, ensure_indexes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ---- Blueprints ----
    from .routes.main import bp as main_bp
    from .routes.auth import bp as auth_bp
    from .routes.participant import bp as participant_bp
    from .routes.coordinator import bp as coordinator_bp
    from .routes.gallery import bp as gallery_bp
    from .routes.results import bp as results_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(participant_bp)
    app.register_blueprint(coordinator_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(results_bp)

    with app.app_context():
        # Warm up a db connection once at boot so indexes exist and,
        # in local/mongomock mode, a bootstrap admin coordinator exists.
        try:
            db = get_db()
            ensure_indexes(db)
            _bootstrap_admin(app, db)
        except Exception as exc:  # noqa: BLE001
            app.logger.warning(f"DB warm-up skipped: {exc}")

    return app


def _bootstrap_admin(app, db):
    from .services.security import hash_password

    coords = db["coordinators"]
    if coords.count_documents({}) == 0:
        username = app.config.get("ADMIN_USER", "admin")
        password = app.config.get("ADMIN_PASS", "admin123")
        coords.insert_one(
            {
                "username": username,
                "password_hash": hash_password(password),
                "name": "System Administrator",
                "role": "admin",
                "assigned_event_slug": "*",
            }
        )
        app.logger.info("Created default bootstrap admin coordinator.")

    # 2) Event Coordinator Demo Account
    if db.users.count_documents({"username": "biotech_coord"}) == 0:
        db.users.insert_one({
            "username": "biotech_coord",
            "password_hash": hash_password("techfinix26"),
            "role": "event_coordinator",
            "name": "Biotech Event Coordinator",
            "assigned_events": ["experiment-detection", "molecule-docking", "biomolecule-puzzle"],
        })

    # 3) Demo Participant Account
    if db.users.count_documents({"participant_id": "TF26-001"}) == 0:
        db.users.insert_one({
            "participant_id": "TF26-001",
            "password_hash": hash_password("techfinix26"),
            "role": "participant",
            "name": "Alex Biotech",
            "email": "alex.biotech@paavai.edu.in",
            "event": "experiment-detection",
            "team": "BioDetectives (Team A)",
        })
