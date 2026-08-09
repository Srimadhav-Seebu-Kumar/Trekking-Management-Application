from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.decorators import role_required
from app.extensions import db
from app.forms import ProfileForm
from app.models import DIFFICULTIES, Booking, Trek

bp = Blueprint("trekker", __name__, url_prefix="/trekker")


@bp.before_request
@login_required
@role_required("trekker")
def guard():
    pass


@bp.route("/dashboard")
def dashboard():
    available_treks = Trek.query.filter_by(status="Open").order_by(Trek.start_date.asc()).limit(6).all()
    my_bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .order_by(Booking.booking_date.desc())
        .limit(6)
        .all()
    )
    return render_template("trekker/dashboard.html", available_treks=available_treks, my_bookings=my_bookings)


@bp.route("/treks")
def browse_treks():
    # Trekkers can view Approved and Open treks; booking itself is only
    # allowed while a trek's status is Open (enforced in book_trek).
    query = Trek.query.filter(Trek.status.in_(("Approved", "Open")))

    location = request.args.get("location", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    q = request.args.get("q", "").strip()

    if q:
        query = query.filter(Trek.name.ilike(f"%{q}%"))
    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))
    if difficulty in DIFFICULTIES:
        query = query.filter_by(difficulty=difficulty)

    treks = query.order_by(Trek.start_date.asc()).all()
    return render_template(
        "trekker/treks.html",
        treks=treks,
        difficulties=DIFFICULTIES,
        q=q,
        location=location,
        difficulty=difficulty,
    )


@bp.route("/treks/<int:trek_id>")
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    existing_booking = Booking.query.filter_by(
        user_id=current_user.id, trek_id=trek.id, status="Booked"
    ).first()
    return render_template("trekker/trek_detail.html", trek=trek, existing_booking=existing_booking)


@bp.route("/treks/<int:trek_id>/book", methods=["POST"])
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.status != "Open":
        flash("This trek is not open for booking.", "danger")
        return redirect(url_for("trekker.trek_detail", trek_id=trek_id))

    already_booked = Booking.query.filter_by(
        user_id=current_user.id, trek_id=trek.id, status="Booked"
    ).first()
    if already_booked:
        flash("You already have an active booking for this trek.", "warning")
        return redirect(url_for("trekker.trek_detail", trek_id=trek_id))

    # Atomic, race-safe slot decrement: only succeeds if a slot is still available.
    updated_rows = (
        db.session.query(Trek)
        .filter(Trek.id == trek_id, Trek.status == "Open", Trek.available_slots > 0)
        .update({Trek.available_slots: Trek.available_slots - 1}, synchronize_session=False)
    )

    if updated_rows == 0:
        db.session.rollback()
        flash("Sorry, this trek just sold out of available slots.", "danger")
        return redirect(url_for("trekker.trek_detail", trek_id=trek_id))

    booking = Booking(user_id=current_user.id, trek_id=trek.id, status="Booked")
    db.session.add(booking)
    db.session.commit()
    flash(f'Trek "{trek.name}" booked successfully!', "success")
    return redirect(url_for("trekker.my_bookings"))


@bp.route("/bookings")
def my_bookings():
    bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .order_by(Booking.booking_date.desc())
        .all()
    )
    return render_template("trekker/bookings.html", bookings=bookings)


@bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash("You can only cancel your own bookings.", "danger")
        return redirect(url_for("trekker.my_bookings"))

    if booking.status != "Booked":
        flash("This booking cannot be cancelled.", "warning")
        return redirect(url_for("trekker.my_bookings"))

    booking.status = "Cancelled"
    trek = booking.trek
    if trek.status != "Completed":
        trek.available_slots = min(trek.total_slots, trek.available_slots + 1)
    db.session.commit()
    flash("Booking cancelled successfully.", "success")
    return redirect(url_for("trekker.my_bookings"))


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
        return redirect(url_for("trekker.profile"))
    return render_template("trekker/profile.html", form=form)
