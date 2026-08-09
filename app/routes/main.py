from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

from app.models import Trek

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        if current_user.is_staff:
            return redirect(url_for("staff.dashboard"))
        return redirect(url_for("trekker.dashboard"))

    featured_treks = (
        Trek.query.filter_by(status="Open").order_by(Trek.start_date.asc()).limit(6).all()
    )
    return render_template("index.html", treks=featured_treks)
