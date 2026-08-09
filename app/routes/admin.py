from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.decorators import role_required
from app.extensions import db
from app.forms import AssignStaffForm, TrekForm
from app.models import Booking, StaffProfile, Trek, User

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
@login_required
@role_required("admin")
def guard():
    """Applies login_required + role_required to every route in this blueprint."""
    pass


@bp.route("/dashboard")
def dashboard():
    stats = {
        "total_treks": Trek.query.count(),
        "total_users": User.query.filter_by(role="trekker").count(),
        "total_staff": User.query.filter_by(role="staff").count(),
        "total_bookings": Booking.query.count(),
        "pending_staff": StaffProfile.query.filter_by(approval_status="Pending").count(),
        "open_treks": Trek.query.filter_by(status="Open").count(),
    }
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(8).all()
    return render_template("admin/dashboard.html", stats=stats, recent_bookings=recent_bookings)


# ---------- Treks ----------

@bp.route("/treks")
def treks():
    all_treks = Trek.query.order_by(Trek.created_at.desc()).all()
    return render_template("admin/treks.html", treks=all_treks)


@bp.route("/treks/new", methods=["GET", "POST"])
def new_trek():
    form = TrekForm()
    if form.validate_on_submit():
        trek = Trek(
            name=form.name.data.strip(),
            location=form.location.data.strip(),
            difficulty=form.difficulty.data,
            duration_days=form.duration_days.data,
            total_slots=form.total_slots.data,
            available_slots=form.total_slots.data,
            status=form.status.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            description=form.description.data,
        )
        db.session.add(trek)
        db.session.commit()
        flash(f'Trek "{trek.name}" created successfully.', "success")
        return redirect(url_for("admin.treks"))
    return render_template("admin/trek_form.html", form=form, title="Add Trek")


@bp.route("/treks/<int:trek_id>/edit", methods=["GET", "POST"])
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    form = TrekForm(obj=trek)
    if form.validate_on_submit():
        slot_delta = form.total_slots.data - trek.total_slots
        trek.name = form.name.data.strip()
        trek.location = form.location.data.strip()
        trek.difficulty = form.difficulty.data
        trek.duration_days = form.duration_days.data
        trek.total_slots = form.total_slots.data
        trek.available_slots = max(0, trek.available_slots + slot_delta)
        trek.status = form.status.data
        trek.start_date = form.start_date.data
        trek.end_date = form.end_date.data
        trek.description = form.description.data
        db.session.commit()
        flash(f'Trek "{trek.name}" updated successfully.', "success")
        return redirect(url_for("admin.treks"))
    return render_template("admin/trek_form.html", form=form, title="Edit Trek", trek=trek)


@bp.route("/treks/<int:trek_id>/delete", methods=["POST"])
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.bookings:
        # Preserve historical booking data instead of hard-deleting.
        trek.status = "Closed"
        db.session.commit()
        flash(f'Trek "{trek.name}" has existing bookings, so it was closed instead of deleted to preserve history.', "warning")
    else:
        db.session.delete(trek)
        db.session.commit()
        flash("Trek removed successfully.", "success")
    return redirect(url_for("admin.treks"))


@bp.route("/treks/<int:trek_id>/assign", methods=["GET", "POST"])
def assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    approved_staff = (
        StaffProfile.query.join(User)
        .filter(StaffProfile.approval_status == "Approved", User.account_status == "Active")
        .all()
    )
    form = AssignStaffForm()
    form.staff_id.choices = [(0, "-- Unassign --")] + [(s.id, f"{s.name} ({s.email})") for s in approved_staff]
    if trek.assigned_staff_id:
        form.staff_id.data = trek.assigned_staff_id

    if form.validate_on_submit():
        trek.assigned_staff_id = form.staff_id.data if form.staff_id.data != 0 else None
        db.session.commit()
        flash(f'Staff assignment updated for "{trek.name}".', "success")
        return redirect(url_for("admin.treks"))

    return render_template("admin/assign_staff.html", form=form, trek=trek)


# ---------- Staff approval / blacklist ----------

@bp.route("/staff")
def staff_list():
    profiles = StaffProfile.query.join(User).order_by(User.created_at.desc()).all()
    return render_template("admin/staff.html", profiles=profiles)


@bp.route("/staff/<int:profile_id>/approve", methods=["POST"])
def approve_staff(profile_id):
    profile = StaffProfile.query.get_or_404(profile_id)
    profile.approval_status = "Approved"
    db.session.commit()
    flash(f"{profile.name} has been approved as trek staff.", "success")
    return redirect(url_for("admin.staff_list"))


@bp.route("/staff/<int:profile_id>/reject", methods=["POST"])
def reject_staff(profile_id):
    profile = StaffProfile.query.get_or_404(profile_id)
    profile.approval_status = "Rejected"
    db.session.commit()
    flash(f"{profile.name}'s registration has been rejected.", "info")
    return redirect(url_for("admin.staff_list"))


@bp.route("/staff/<int:profile_id>/blacklist", methods=["POST"])
def blacklist_staff(profile_id):
    profile = StaffProfile.query.get_or_404(profile_id)
    profile.user.account_status = "Blacklisted"
    db.session.commit()
    flash(f"{profile.name} has been blacklisted.", "warning")
    return redirect(url_for("admin.staff_list"))


@bp.route("/staff/<int:profile_id>/reinstate", methods=["POST"])
def reinstate_staff(profile_id):
    profile = StaffProfile.query.get_or_404(profile_id)
    profile.user.account_status = "Active"
    db.session.commit()
    flash(f"{profile.name} has been reinstated.", "success")
    return redirect(url_for("admin.staff_list"))


# ---------- Users (trekkers) ----------

@bp.route("/users")
def users_list():
    trekkers = User.query.filter_by(role="trekker").order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=trekkers)


@bp.route("/users/<int:user_id>/blacklist", methods=["POST"])
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.account_status = "Blacklisted"
    db.session.commit()
    flash(f"{user.name} has been blacklisted.", "warning")
    return redirect(url_for("admin.users_list"))


@bp.route("/users/<int:user_id>/reinstate", methods=["POST"])
def reinstate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.account_status = "Active"
    db.session.commit()
    flash(f"{user.name} has been reinstated.", "success")
    return redirect(url_for("admin.users_list"))


# ---------- Bookings ----------

@bp.route("/bookings")
def bookings():
    all_bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template("admin/bookings.html", bookings=all_bookings)


# ---------- Search ----------

@bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    treks_found, staff_found, users_found = [], [], []
    if q:
        like = f"%{q}%"
        trek_query = Trek.query.filter(Trek.name.ilike(like) | Trek.location.ilike(like))
        if q.isdigit():
            trek_query = trek_query.union(Trek.query.filter(Trek.id == int(q)))
        treks_found = trek_query.all()

        staff_query = StaffProfile.query.join(User).filter(User.name.ilike(like))
        if q.isdigit():
            staff_query = staff_query.union(StaffProfile.query.filter(StaffProfile.id == int(q)))
        staff_found = staff_query.all()

        user_query = User.query.filter_by(role="trekker").filter(User.name.ilike(like))
        if q.isdigit():
            user_query = user_query.union(User.query.filter_by(role="trekker").filter(User.id == int(q)))
        users_found = user_query.all()

    return render_template(
        "admin/search.html", q=q, treks=treks_found, staff=staff_found, users=users_found
    )
