from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from ..services.mongodb import get_db
from ..services.security import verify_password

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mode = request.form.get("mode", "participant")
        db = get_db()

        try:
            if mode == "participant":
                pid = request.form.get("participant_id", "").strip().upper()
                password = request.form.get("password", "")
                user = db.users.find_one({"participant_id": pid, "role": "participant"})
                if user and verify_password(user["password_hash"], password):
                    session["user"] = {
                        "id": str(user["_id"]),
                        "participant_id": user["participant_id"],
                        "name": user.get("name", ""),
                        "role": "participant",
                        "event": user.get("event"),
                        "team": user.get("team"),
                    }
                    flash(f"Welcome back, {user.get('name', pid)}!", "success")
                    return redirect(request.args.get("next") or url_for("participant.dashboard"))
                flash("Invalid participant ID or password.", "error")

            else:  # coordinator
                username = request.form.get("username", "").strip().lower()
                password = request.form.get("password", "")
                user = db.users.find_one({"username": username, "role": {"$in": ["super_coordinator", "event_coordinator"]}})
                if user and verify_password(user["password_hash"], password):
                    session["user"] = {
                        "id": str(user["_id"]),
                        "username": user["username"],
                        "name": user.get("name", username),
                        "role": user["role"],
                        "assigned_events": user.get("assigned_events", []),
                    }
                    flash(f"Welcome back, {user.get('name', username)}!", "success")
                    return redirect(request.args.get("next") or url_for("coordinator.dashboard"))
                flash("Invalid coordinator username or password.", "error")
        except Exception as exc:
            flash(f"Database connection error: {exc}. Please check your MongoDB Atlas Network Access IP whitelist.", "error")

        return redirect(url_for("auth.login"))

    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("You've been logged out.", "success")
    return redirect(url_for("main.index"))
