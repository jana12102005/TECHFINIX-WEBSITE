from flask import Blueprint, render_template

from ..services.mongodb import get_db

bp = Blueprint("results", __name__)


@bp.route("/results")
def index():
    db = get_db()
    events = list(db.events.find({}).sort("order", 1))
    published = {r["event_slug"]: r for r in db.results.find({"published": True})}
    return render_template("results.html", events=events, published=published)
