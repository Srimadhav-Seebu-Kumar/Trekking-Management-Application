from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.forms import LoginForm, RegisterForm
from app.models import StaffProfile, User

bp = Blueprint("auth", __name__)


def _redirect_for_role(user):
    if user.is_admin:
        return redirect(url_for("admin.dashboard"))
    if user.is_staff:
        return redirect(url_for("staff.dashboard"))
    return redirect(url_for("trekker.dashboard"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user)

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing:
            flash("An account with that email already exists.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            contact=form.contact.data.strip(),
            role=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # assigns user.id before creating dependent staff profile

        if user.role == "staff":
            profile = StaffProfile(user_id=user.id, approval_status="Pending")
            db.session.add(profile)

        db.session.commit()

        if user.role == "staff":
            flash("Registration successful! Your account needs admin approval before you can access the dashboard.", "success")
        else:
            flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)
        if user.account_status == "Blacklisted":
            flash("Your account has been blacklisted. Contact the administrator.", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user)
        flash(f"Welcome back, {user.name}!", "success")
        return _redirect_for_role(user)

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
