import string
import secrets
from functools import wraps

from flask import session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash

hash_password = generate_password_hash
verify_password = check_password_hash


def generate_temp_password(length=8):
    """Readable temp password like TX26-A7K9P style token."""
    alphabet = string.ascii_uppercase + string.digits
    chunk = "".join(secrets.choice(alphabet) for _ in range(5))
    return f"TX26-{chunk}"


def current_user():
    return session.get("user")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = session.get("user")
            if not user:
                flash("Please log in to continue.", "error")
                return redirect(url_for("auth.login", next=request.path))
            if user.get("role") not in roles:
                flash("You don't have access to that page.", "error")
                return redirect(url_for("main.index"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def coordinator_can_manage(user, event_slug):
    if user.get("role") == "super_coordinator":
        return True
    assigned = user.get("assigned_events") or []
    if not assigned:
        return True
    return event_slug in assigned
