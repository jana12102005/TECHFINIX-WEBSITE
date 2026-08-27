from flask import Blueprint, render_template, request, session

from ..services.mongodb import get_db
from ..services.security import login_required, current_user

bp = Blueprint("gallery", __name__)


@bp.route("/gallery")
@login_required
def index():
    db = get_db()
    user = current_user()
    event_filter = request.args.get("event", "")

    # If logged in as participant and no event filter was clicked, default to participant's event
    if user.get("role") == "participant" and not event_filter and user.get("event"):
        event_filter = user.get("event")

    query = {"event_slug": event_filter} if event_filter else {}
    photos = list(db.photos.find(query).sort("uploaded_at", -1))
    events = list(db.events.find({}).sort("order", 1))
    return render_template("gallery.html", photos=photos, events=events, active_event=event_filter)
