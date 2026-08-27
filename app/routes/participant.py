import io
import zipfile
import urllib.request

from flask import Blueprint, render_template, send_file, abort

from ..services.mongodb import get_db
from ..services.security import login_required, current_user

bp = Blueprint("participant", __name__, url_prefix="/participant")


def _my_photos(db, user):
    """Photos tagged directly to this participant, or belonging to their event."""
    clauses = [{"tagged_participants": user.get("participant_id")}]
    if user.get("event"):
        clauses.append({"event_slug": user.get("event")})
    else:
        # If participant profile has no specific event assigned, allow viewing all photos
        return list(db.photos.find({}).sort("uploaded_at", -1))
    
    return list(db.photos.find({"$or": clauses}).sort("uploaded_at", -1))


@bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    if user.get("role") != "participant":
        abort(403)
    db = get_db()
    photos = _my_photos(db, user)
    my_event = db.events.find_one({"slug": user.get("event")}) if user.get("event") else None
    published_results = {r["event_slug"]: r for r in db.results.find({"published": True})}
    all_events = list(db.events.find({}).sort("order", 1))
    return render_template(
        "participant_dashboard.html",
        user=user,
        photos=photos,
        my_event=my_event,
        published_results=published_results,
        all_events=all_events,
    )


@bp.route("/photos/download-all")
@login_required
def download_all():
    user = current_user()
    if user.get("role") != "participant":
        abort(403)
    db = get_db()
    photos = _my_photos(db, user)
    if not photos:
        abort(404)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, photo in enumerate(photos, start=1):
            try:
                url = photo["url"]
                if url.startswith("http"):
                    with urllib.request.urlopen(url, timeout=10) as resp:
                        data = resp.read()
                else:
                    # local static path — read straight off disk
                    from flask import current_app
                    disk_path = url.replace("/static/", "app/static/", 1).lstrip("/")
                    with open(disk_path, "rb") as f:
                        data = f.read()
                ext = url.rsplit(".", 1)[-1].split("?")[0][:5]
                zf.writestr(f"techfinix26_photo_{i:03d}.{ext}", data)
            except Exception:
                continue
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"TECHFINIX26_{user['participant_id']}_photos.zip",
    )
