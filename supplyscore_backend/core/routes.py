from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from .models import User, Review
from sqlalchemy.exc import SQLAlchemyError
from .db import db


core_bp = Blueprint(
    "core",
    __name__,
    template_folder="templates",
)


@core_bp.app_template_global()
def static_url(path: str) -> str:
    return url_for("static", filename=path)


@core_bp.route("/")
def home():
    return render_template("core/home.html")


@core_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_role"] = user.role
            flash("Logged in successfully.", "success")
            return redirect(url_for("core.home"))
        flash("Invalid credentials.", "danger")
    return render_template("core/login.html")


@core_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "vendor")
        # Prevent creating admin via public registration
        if role == "admin":
            role = "vendor"

        if not username or not email or not password:
            flash("All fields are required.", "warning")
            return render_template("core/register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return render_template("core/register.html")

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("core.login"))
    return render_template("core/register.html")


@core_bp.route("/vendor-review", methods=["GET", "POST"])
def vendor_review():
    if not session.get("user_id") or session.get("user_role") != "business":
        flash("Only logged-in business users can access this page.", "danger")
        return redirect(url_for("core.login"))

    # Get user's reviews for display
    user_reviews = Review.query.filter_by(business_id=session.get("user_id")).order_by(Review.created_at.desc()).all()
    
    if request.method == "POST":
        vendor_id = request.form.get("vendor_id")
        submitted_user_id = request.form.get("user_id")
        quality = request.form.get("quality")
        cost_effectiveness = request.form.get("cost_effectiveness")
        delivery_speed = request.form.get("delivery_speed")
        compliance = request.form.get("compliance")
        comments = request.form.get("comments", "").strip()

        try:
            vendor_id_int = int(vendor_id) if vendor_id is not None else None
            submitted_user_id_int = int(submitted_user_id) if submitted_user_id is not None else None
            quality_int = int(quality) if quality is not None else None
            cost_effectiveness_int = int(cost_effectiveness) if cost_effectiveness is not None else None
            delivery_speed_int = int(delivery_speed) if delivery_speed is not None else None
            compliance_int = int(compliance) if compliance is not None else None
        except ValueError:
            flash("Invalid numeric values provided.", "danger")
            return render_template("core/vendor_review.html", user_reviews=user_reviews)

        def valid_star(value: int) -> bool:
            return value is not None and 1 <= value <= 5

        if not all([
            vendor_id_int is not None,
            valid_star(quality_int),
            valid_star(cost_effectiveness_int),
            valid_star(delivery_speed_int),
            valid_star(compliance_int),
        ]):
            flash("Please provide valid 1–5 ratings for all categories and a vendor ID.", "warning")
            return render_template("core/vendor_review.html", user_reviews=user_reviews)

        # Ensure the hidden user_id matches logged-in business to prevent tampering
        business_id_int = session.get("user_id")
        if submitted_user_id_int and submitted_user_id_int != business_id_int:
            flash("Session mismatch detected. Please try again.", "danger")
            return render_template("core/vendor_review.html", user_reviews=user_reviews)

        # Verify vendor exists
        vendor = User.query.get(vendor_id_int)
        if vendor is None or vendor.role != "vendor":
            flash("Please provide a valid vendor ID.", "warning")
            return render_template("core/vendor_review.html", user_reviews=user_reviews)

        # Create and persist review
        review = Review(
            business_id=business_id_int,
            vendor_id=vendor_id_int,
            quality_rating=quality_int,
            cost_rating=cost_effectiveness_int,
            delivery_rating=delivery_speed_int,
            compliance_rating=compliance_int,
            comments=comments or None,
        )
        try:
            db.session.add(review)
            db.session.commit()
        except SQLAlchemyError as exc:
            db.session.rollback()
            flash(f"Database error while saving review: {exc.__class__.__name__}", "danger")
            return render_template("core/vendor_review.html", user_reviews=user_reviews)

        flash("Review submitted successfully.", "success")
        return redirect(url_for("core.vendor_review"))
    
    return render_template("core/vendor_review.html", user_reviews=user_reviews)


@core_bp.route("/quote-comparison", methods=["GET", "POST"])
def quote_comparison():
    if request.method == "POST":
        flash("Quote submitted (demo).", "info")
        return redirect(url_for("core.home"))
    return render_template("core/quote_comparison.html")


@core_bp.route("/disputes", methods=["GET", "POST"])
def dispute_management():
    if request.method == "POST":
        flash("Dispute submitted (demo).", "info")
        return redirect(url_for("core.home"))
    return render_template("core/dispute_management.html")


@core_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("core.login"))



# Admin: Users list and delete
@core_bp.route("/users")
def users():
    if session.get("user_role") != "admin":
        flash("Unauthorized.", "danger")
        return redirect(url_for("core.home"))
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("core/users.html", users=all_users)


@core_bp.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id: int):
    if session.get("user_role") != "admin":
        flash("Unauthorized.", "danger")
        return redirect(url_for("core.home"))
    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("core.users"))
    if session.get("user_id") == user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for("core.users"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for("core.users"))


@core_bp.route("/users/create-admin", methods=["GET", "POST"])
def create_admin():
    # Allow bootstrapping: if there is no admin yet, permit access without login
    has_admin = User.query.filter_by(role="admin").first() is not None
    if has_admin and session.get("user_role") != "admin":
        flash("Unauthorized.", "danger")
        return redirect(url_for("core.home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "warning")
            return render_template("core/create_admin.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return render_template("core/create_admin.html")

        admin_user = User(username=username, email=email, role="admin")
        admin_user.set_password(password)
        try:
            db.session.add(admin_user)
            db.session.commit()
        except SQLAlchemyError as exc:
            db.session.rollback()
            flash(f"Database error: {exc.__class__.__name__}", "danger")
            return render_template("core/create_admin.html")

        flash("Admin user created.", "success")
        if session.get("user_role") == "admin":
            return redirect(url_for("core.users"))
        return redirect(url_for("core.login"))

    return render_template("core/create_admin.html", has_admin=has_admin)


@core_bp.route("/reviews/<int:review_id>/delete", methods=["POST"])
def delete_review(review_id: int):
    if not session.get("user_id") or session.get("user_role") != "business":
        flash("Unauthorized.", "danger")
        return redirect(url_for("core.login"))
    
    review = Review.query.get(review_id)
    if not review:
        flash("Review not found.", "warning")
        return redirect(url_for("core.vendor_review"))
    
    # Ensure the user can only delete their own reviews
    if review.business_id != session.get("user_id"):
        flash("You can only delete your own reviews.", "danger")
        return redirect(url_for("core.vendor_review"))
    
    try:
        db.session.delete(review)
        db.session.commit()
        flash("Review deleted successfully.", "success")
    except SQLAlchemyError as exc:
        db.session.rollback()
        flash(f"Database error while deleting review: {exc.__class__.__name__}", "danger")
    
    return redirect(url_for("core.vendor_review"))

