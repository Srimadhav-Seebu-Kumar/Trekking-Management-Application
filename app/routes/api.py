"""Read-only JSON API resources (recommended/optional functionality).

Trek listing/detail is public; user and booking resources require an
authenticated admin session.
"""

from flask import Blueprint, jsonify
from flask_login import current_user

from app.models import Booking, Trek, User

bp = Blueprint("api", __name__, url_prefix="/api")


def _trek_to_dict(trek):
    return {
        "id": trek.id,
        "name": trek.name,
        "location": trek.location,
        "difficulty": trek.difficulty,
        "duration_days": trek.duration_days,
        "total_slots": trek.total_slots,
        "available_slots": trek.available_slots,
        "assigned_staff_id": trek.assigned_staff_id,
        "status": trek.status,
        "start_date": trek.start_date.isoformat(),
        "end_date": trek.end_date.isoformat(),
    }


def _admin_only():
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required."}), 401
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required."}), 403
    return None


@bp.route("/treks")
def treks():
    all_treks = Trek.query.filter(Trek.status.in_(("Approved", "Open"))).order_by(Trek.start_date.asc()).all()
    return jsonify({"treks": [_trek_to_dict(t) for t in all_treks]})


@bp.route("/treks/<int:trek_id>")
def trek_detail(trek_id):
    trek = Trek.query.get(trek_id)
    if trek is None:
        return jsonify({"error": "Trek not found."}), 404
    return jsonify(_trek_to_dict(trek))


@bp.route("/users")
def users():
    denied = _admin_only()
    if denied:
        return denied
    all_users = User.query.order_by(User.id.asc()).all()
    return jsonify(
        {
            "users": [
                {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "role": u.role,
                    "account_status": u.account_status,
                }
                for u in all_users
            ]
        }
    )


@bp.route("/bookings")
def bookings():
    denied = _admin_only()
    if denied:
        return denied
    all_bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return jsonify(
        {
            "bookings": [
                {
                    "id": b.id,
                    "user_id": b.user_id,
                    "trek_id": b.trek_id,
                    "booking_date": b.booking_date.isoformat(),
                    "status": b.status,
                }
                for b in all_bookings
            ]
        }
    )
