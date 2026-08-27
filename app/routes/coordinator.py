import base64
import re
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify

from ..services.mongodb import get_db
from ..services.security import role_required, current_user, coordinator_can_manage
from ..services.storage import save_photo, save_photo_bytes

bp = Blueprint("coordinator", __name__, url_prefix="/coordinator")

ROLES = ("super_coordinator", "event_coordinator")


DEFAULT_EVENTS = [
    {"slug": "project-expo", "name": "Project Expo", "category": "technical", "order": 1, "day": "Day 1 · 10 September 2026", "status": "upcoming"},
    {"slug": "paper-presentation", "name": "Paper Presentation", "category": "technical", "order": 2, "day": "Day 1 · 10 September 2026", "status": "upcoming"},
    {"slug": "experiment-detection", "name": "Experiment Detection Challenge", "category": "non_technical", "order": 3, "day": "Day 2 · 11 September 2026", "status": "upcoming"},
    {"slug": "molecule-docking", "name": "Molecule Docking Challenge", "category": "non_technical", "order": 4, "day": "Day 2 · 11 September 2026", "status": "upcoming"},
    {"slug": "biomolecule-puzzle", "name": "Biomolecule Puzzle", "category": "non_technical", "order": 5, "day": "Day 2 · 11 September 2026", "status": "upcoming"},
]


def _ensure_events_exist(db):
    if db.events.count_documents({}) == 0:
        for ev in DEFAULT_EVENTS:
            ev["updated_at"] = datetime.now(timezone.utc)
            db.events.update_one({"slug": ev["slug"]}, {"$set": ev}, upsert=True)


def _visible_events(db, user):
    _ensure_events_exist(db)
    all_events = list(db.events.find({}).sort("order", 1))
    if user.get("role") == "super_coordinator":
        return all_events
    assigned_slugs = user.get("assigned_events", [])
    if assigned_slugs:
        filtered = [e for e in all_events if e["slug"] in assigned_slugs]
        if filtered:
            return filtered
    return all_events


@bp.route("/dashboard")
@role_required(*ROLES)
def dashboard():
    user = current_user()
    db = get_db()
    events = _visible_events(db, user)
    results_by_slug = {r["event_slug"]: r for r in db.results.find({})}
    recent_photos = list(db.photos.find({}).sort("uploaded_at", -1).limit(24))
    return render_template(
        "coordinator_dashboard.html",
        user=user,
        events=events,
        results_by_slug=results_by_slug,
        recent_photos=recent_photos,
    )


@bp.route("/photos/upload", methods=["POST"])
@role_required(*ROLES)
def upload_photo():
    user = current_user()
    db = get_db()
    event_slug = request.form.get("event_slug", "").strip()
    if not event_slug:
        events = _visible_events(db, user)
        event_slug = events[0]["slug"] if events else "general"

    if not coordinator_can_manage(user, event_slug):
        flash("You aren't assigned to that event.", "error")
        return redirect(url_for("coordinator.dashboard"))

    saved_any = False

    try:
        # 1) Regular file upload (one or many)
        for f in request.files.getlist("photos"):
            if f and f.filename:
                result = save_photo(f, folder=event_slug)
                _insert_photo(db, result, event_slug, user)
                saved_any = True

        # 2) Live camera capture — base64 data URL from <canvas>.toDataURL()
        capture_data_url = request.form.get("capture_data_url")
        if capture_data_url:
            match = re.match(r"data:image/(\w+);base64,(.+)", capture_data_url)
            if match:
                ext, b64data = match.groups()
                raw = base64.b64decode(b64data)
                result = save_photo_bytes(raw, filename=f"capture.{ext}", folder=event_slug)
                _insert_photo(db, result, event_slug, user)
                saved_any = True
    except Exception as exc:
        flash(f"Error processing photo upload: {exc}", "error")
        return redirect(url_for("coordinator.dashboard"))

    if saved_any:
        flash("Photo(s) uploaded successfully to the gallery.", "success")
    else:
        flash("No photo was received — please choose a file or capture one.", "error")
    return redirect(url_for("coordinator.dashboard"))


@bp.route("/photos/delete/<photo_id>", methods=["POST"])
@role_required(*ROLES)
def delete_photo_route(photo_id):
    user = current_user()
    if user.get("role") != "super_coordinator":
        flash("Only super coordinators can delete photos.", "error")
        return redirect(request.referrer or url_for("coordinator.dashboard"))

    db = get_db()
    from bson.objectid import ObjectId
    try:
        query = {"_id": ObjectId(photo_id)}
    except Exception:
        query = {"_id": photo_id}

    photo = db.photos.find_one(query)
    if photo:
        try:
            delete_photo(photo.get("public_id"), photo.get("backend", "local"))
        except Exception:
            pass
        db.photos.delete_one(query)
        flash("Photo deleted from gallery.", "success")
    else:
        flash("Photo not found.", "error")

    return redirect(request.referrer or url_for("coordinator.dashboard"))


def _insert_photo(db, storage_result, event_slug, user):
    db.photos.insert_one({
        "event_slug": event_slug,
        "url": storage_result["url"],
        "public_id": storage_result["public_id"],
        "backend": storage_result["backend"],
        "uploaded_by": user.get("username"),
        "uploaded_at": datetime.now(timezone.utc),
        "tagged_participants": [],
    })


@bp.route("/results/<event_slug>", methods=["POST"])
@role_required(*ROLES)
def update_results(event_slug):
    user = current_user()
    if not coordinator_can_manage(user, event_slug):
        flash("You aren't assigned to that event.", "error")
        return redirect(url_for("coordinator.dashboard"))

    db = get_db()
    winners_raw = request.form.get("winners", "").strip()
    summary = request.form.get("summary", "").strip()
    publish = request.form.get("publish") == "on"

    winners = [line.strip() for line in winners_raw.splitlines() if line.strip()]

    db.results.update_one(
        {"event_slug": event_slug},
        {"$set": {
            "event_slug": event_slug,
            "winners": winners,
            "summary": summary,
            "published": publish,
            "updated_by": user.get("username"),
            "updated_at": datetime.now(timezone.utc),
        }},
        upsert=True,
    )
    flash(
        "Results published to the public Results page." if publish
        else "Results saved as a draft (not visible to the public yet).",
        "success",
    )
    return redirect(url_for("coordinator.dashboard"))


@bp.route("/events/<event_slug>/status", methods=["POST"])
@role_required(*ROLES)
def update_event_status(event_slug):
    user = current_user()
    if not coordinator_can_manage(user, event_slug):
        abort(403)
    db = get_db()
    status = request.form.get("status", "upcoming")
    if status not in ("upcoming", "live", "completed"):
        abort(400)
    db.events.update_one({"slug": event_slug}, {"$set": {"status": status}})
    flash(f"Event status updated to {status.upper()}.", "success")
    return redirect(url_for("coordinator.dashboard"))
