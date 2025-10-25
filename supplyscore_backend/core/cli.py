from __future__ import annotations

import click

from .models import User
from .db import db


def register_cli(app):
    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.option("--username", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(email: str, username: str, password: str):
        """Create an admin user."""
        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            click.echo("User with this email already exists.")
            return
        user = User(email=email, username=username.strip(), role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Admin created.")







