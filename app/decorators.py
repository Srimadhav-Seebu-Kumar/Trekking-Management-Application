from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
    """Restrict a view to users whose `role` is in `roles`. Assumes @login_required already applied."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def approved_staff_required(view_func):
    """Restrict a view to staff whose profile has been approved by admin."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_staff:
            abort(403)
        profile = current_user.staff_profile
        if profile is None or profile.approval_status != "Approved":
            flash("Your staff account is awaiting admin approval before you can access the dashboard.", "warning")
            return redirect(url_for("staff.dashboard"))
        return view_func(*args, **kwargs)

    return wrapped
