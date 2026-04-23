from __future__ import annotations

import re

import click
from flask import Flask
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import ValidationError
from app.core.security import hash_password
from app.extensions import db
from app.models import User
from app.utils.validators import normalize_email, validate_password_strength

_MAX_NAME_LENGTH = 150
_MAX_EMAIL_LENGTH = 255
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def register_commands(app: Flask) -> None:
    @app.cli.command("create-admin")
    @click.option("--name", prompt=True, help="Nome do administrador.")
    @click.option("--email", prompt=True, help="E-mail do administrador.")
    @click.option(
        "--password",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="Senha do administrador.",
    )
    def create_admin(name: str, email: str, password: str) -> None:
        normalized_name = _normalize_name(name)
        normalized_email = normalize_email(email)
        _validate_create_admin_input(
            name=normalized_name,
            email=normalized_email,
            password=password,
        )

        try:
            existing = db.session.execute(
                db.select(User.id).where(User.email == normalized_email)
            ).scalar_one_or_none()
            if existing is not None:
                raise click.ClickException("Já existe usuário com esse e-mail.")

            user = User(
                name=normalized_name,
                email=normalized_email,
                password_hash=hash_password(password),
                is_admin=True,
                is_active=True,
            )
            db.session.add(user)
            db.session.commit()
        except click.ClickException:
            db.session.rollback()
            raise
        except IntegrityError as exc:
            db.session.rollback()
            raise click.ClickException(
                "Não foi possível criar o admin porque o e-mail já está em uso."
            ) from exc
        except SQLAlchemyError as exc:
            db.session.rollback()
            raise click.ClickException(
                "Erro de banco de dados ao criar o admin."
            ) from exc
        finally:
            db.session.remove()

        click.echo(f"Admin criado: {user.email}")


def _normalize_name(value: str) -> str:
    return " ".join(value.strip().split())


def _validate_create_admin_input(*, name: str, email: str, password: str) -> None:
    if not name:
        raise click.ClickException("O nome é obrigatório.")

    if len(name) > _MAX_NAME_LENGTH:
        raise click.ClickException("O nome informado é muito longo.")

    if not email or not _EMAIL_RE.match(email):
        raise click.ClickException("Informe um e-mail válido.")

    if len(email) > _MAX_EMAIL_LENGTH:
        raise click.ClickException("O e-mail informado é muito longo.")

    if not password:
        raise click.ClickException("A senha é obrigatória.")

    try:
        validate_password_strength(password)
    except ValidationError as exc:
        detail_message = (exc.details or {}).get("new_password") or exc.message
        raise click.ClickException(detail_message) from exc
