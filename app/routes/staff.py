from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.decorators import approved_staff_required, role_required
from app.extensions import db
from app.forms import ProfileForm, StaffTrekUpdateForm
from app.models import Trek

bp = Blueprint("staff", __name__, url_prefix="/staff")


@bp.before_request
@login_required
@role_required("staff")
def guard():
    pass


def _own_trek_or_404(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    profile = current_user.staff_profile
    if profile is None or trek.assigned_staff_id != profile.id:
        abort(403)
    return trek


@bp.route("/dashboard")
def dashboard():
    profile = current_user.staff_profile
    if profile is None or profile.approval_status != "Approved":
        return render_template("staff/dashboard.html", profile=profile, treks=None)

    assigned_treks = Trek.query.filter_by(assigned_staff_id=profile.id).order_by(Trek.start_date.asc()).all()
    return render_template("staff/dashboard.html", profile=profile, treks=assigned_treks)


@bp.route("/treks/<int:trek_id>")
@approved_staff_required
def trek_detail(trek_id):
    trek = _own_trek_or_404(trek_id)
    form = StaffTrekUpdateForm(
        obj=trek,
        status=trek.status if trek.status in ("Open", "Closed", "Started", "Completed") else "Open",
    )
    participants = trek.active_bookings
    return render_template("staff/trek_detail.html", trek=trek, form=form, participants=participants)


@bp.route("/treks/<int:trek_id>/update", methods=["POST"])
@approved_staff_required
def update_trek(trek_id):
    trek = _own_trek_or_404(trek_id)
    form = StaffTrekUpdateForm()
    if form.validate_on_submit():
        if form.available_slots.data > trek.total_slots:
            flash(f"Available slots cannot exceed total slots ({trek.total_slots}).", "danger")
        else:
            trek.available_slots = form.available_slots.data
            trek.status = form.status.data
            if trek.status == "Completed":
                # Completing a trek moves every active booking into the
                # trekkers' history as Completed.
                for booking in trek.bookings:
                    if booking.status == "Booked":
                        booking.status = "Completed"
            db.session.commit()
            flash(f'Trek "{trek.name}" updated successfully.', "success")
        return redirect(url_for("staff.trek_detail", trek_id=trek.id))

    participants = trek.active_bookings
    return render_template("staff/trek_detail.html", trek=trek, form=form, participants=participants)


@bp.route("/profile", methods=["GET", "POST"])
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.contact = form.contact.data.strip()
        if form.password.data:
            current_user.set_password(form.password.data)
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("staff.profile"))
    return render_template("staff/profile.html", form=form)
