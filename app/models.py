from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

# --- Enumerated values (kept as plain strings for SQLite simplicity) ---
ROLES = ("admin", "staff", "trekker")
ACCOUNT_STATUSES = ("Active", "Blacklisted")
STAFF_APPROVAL_STATUSES = ("Pending", "Approved", "Rejected")
DIFFICULTIES = ("Easy", "Moderate", "Hard")
TREK_STATUSES = ("Pending", "Approved", "Open", "Closed", "Started", "Completed")
BOOKING_STATUSES = ("Booked", "Cancelled", "Completed")


class User(UserMixin, db.Model):
    """Single table for all three roles: admin, staff, trekker."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="trekker")
    account_status = db.Column(db.String(20), nullable=False, default="Active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    staff_profile = db.relationship(
        "StaffProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    bookings = db.relationship(
        "Booking", back_populates="user", cascade="all, delete-orphan", foreign_keys="Booking.user_id"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self):
        # Overrides Flask-Login's UserMixin.is_active: blacklisted accounts cannot log in.
        return self.account_status == "Active"

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_staff(self):
        return self.role == "staff"

    @property
    def is_trekker(self):
        return self.role == "trekker"

    def __repr__(self):
        return f"<User {self.id} {self.email} ({self.role})>"


class StaffProfile(db.Model):
    __tablename__ = "staff_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    approval_status = db.Column(db.String(20), nullable=False, default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="staff_profile")
    assigned_treks = db.relationship("Trek", back_populates="assigned_staff")

    @property
    def name(self):
        return self.user.name

    @property
    def contact(self):
        return self.user.contact

    @property
    def email(self):
        return self.user.email

    @property
    def status(self):
        """Effective status shown to admin: blacklist overrides approval state."""
        if self.user.account_status == "Blacklisted":
            return "Blacklisted"
        return self.approval_status

    def __repr__(self):
        return f"<StaffProfile {self.id} user={self.user_id} status={self.approval_status}>"


class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default="Easy")
    duration_days = db.Column(db.Integer, nullable=False, default=1)
    total_slots = db.Column(db.Integer, nullable=False, default=0)
    available_slots = db.Column(db.Integer, nullable=False, default=0)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("staff_profiles.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assigned_staff = db.relationship("StaffProfile", back_populates="assigned_treks")
    bookings = db.relationship("Booking", back_populates="trek", cascade="all, delete-orphan")

    @property
    def active_bookings(self):
        return [b for b in self.bookings if b.status in ("Booked", "Completed")]

    @property
    def registered_count(self):
        return len(self.active_bookings)

    def __repr__(self):
        return f"<Trek {self.id} {self.name} status={self.status}>"


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default="Booked")

    user = db.relationship("User", back_populates="bookings", foreign_keys=[user_id])
    trek = db.relationship("Trek", back_populates="bookings")

    # Note: no unique constraint on (user_id, trek_id) — a user may cancel and
    # re-book the same trek later, and both records must be kept for history.

    def __repr__(self):
        return f"<Booking {self.id} user={self.user_id} trek={self.trek_id} status={self.status}>"
