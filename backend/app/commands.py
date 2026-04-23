from __future__ import annotations

import click
from flask import Flask

from app.core.security import hash_password
from app.extensions import db
from app.models import User


def register_commands(app: Flask) -> None:
    @app.cli.command("create-admin")
    @click.option("--name", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(name: str, email: str, password: str):
        existing = db.session.execute(
            db.select(User).where(User.email == email.strip().lower())
        ).scalar_one_or_none()
        if existing:
            raise click.ClickException("Já existe usuário com esse e-mail.")
        user = User(
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=hash_password(password),
            is_admin=True,
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin criado: {user.email}")
