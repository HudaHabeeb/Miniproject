from __future__ import annotations

from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from .db import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="vendor")  # 'admin' | 'business' | 'vendor'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    reviews_given = db.relationship("Review", foreign_keys="Review.business_id", backref="business_user", lazy="dynamic")
    reviews_received = db.relationship("Review", foreign_keys="Review.vendor_id", backref="vendor_user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Review(db.Model):
    __tablename__ = "reviews"

    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    business_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    quality_rating = db.Column(db.Integer, nullable=False)
    cost_rating = db.Column(db.Integer, nullable=False)
    delivery_rating = db.Column(db.Integer, nullable=False)
    compliance_rating = db.Column(db.Integer, nullable=False)

    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def get_overall_rating(self) -> float:
        """Calculate the overall rating as average of all ratings."""
        return (self.quality_rating + self.cost_rating + self.delivery_rating + self.compliance_rating) / 4

    def to_dict(self) -> dict:
        """Convert review to dictionary for easy serialization."""
        return {
            'review_id': self.review_id,
            'business_id': self.business_id,
            'vendor_id': self.vendor_id,
            'quality_rating': self.quality_rating,
            'cost_rating': self.cost_rating,
            'delivery_rating': self.delivery_rating,
            'compliance_rating': self.compliance_rating,
            'overall_rating': self.get_overall_rating(),
            'comments': self.comments,
            'created_at': self.created_at.isoformat()
        }


