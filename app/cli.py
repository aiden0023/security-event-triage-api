import click
from flask import Flask, current_app
from flask.cli import AppGroup

from app.extensions import db
from app.models import Organization
from app.models.user import ROLE_ADMIN, ROLE_ANALYST, User
from app.services.password import hash_password

DEMO_ORGS = ("Company A", "Company B", "Company C")

seed_cli = AppGroup("seed", help="Seed the database with example data.")


@seed_cli.command("provider")
@click.option("--org-name", required=True, help="Name of the provider organization.")
@click.option("--admin-email", required=True, help="Email of the provider organization.")
@click.option(
    "--password",
    envvar="SEED_PASSWORD",
    required=True,
    help="Password of the admin user. Reads from SEED_PASSWORD if not passed.",
)
def seed_provider(org_name: str, admin_email: str, password: str) -> None:
    """Bootstrap the provider organization and the first admin user."""
    click.confirm(
        f"Create provider org {org_name} with admin user {admin_email.lower()} in "
        f"{current_app.config["CONFIG_NAME"]}?",
        abort=True,
    )
    db_exists = db.session.scalar(db.select(Organization).filter_by(is_provider=True))
    if db_exists is not None and db_exists.name != org_name:
        raise click.ClickException(
            f"Provider org {db_exists.name} already exists."
        )

    created: list[str] = []
    skipped: list[str] = []

    org, made = _get_or_create_org(org_name=org_name, is_provider=True)
    (created if made else skipped).append(f"org {org.name} (provider)")

    _, made = _get_or_create_user(email=admin_email, org=org, role=ROLE_ADMIN, password=password)
    (created if made else skipped).append(f"user {admin_email.lower()} (admin)")

    db.session.commit()
    _report(created, skipped)


@seed_cli.command("demo")
@click.option(
    "--password",
    envvar="SEED_PASSWORD",
    required=True,
    help="Password for every demo user. Reads from SEED_PASSWORD if not passed.",
)
def seed_demo(password: str) -> None:
    """Creates three demo customer orgs; each org has one admin user and one analyst user."""
    _require_non_prod()
    if db.session.scalar(db.select(Organization).filter_by(is_provider=True)) is None:
        raise click.ClickException("No provider orgs exist yet. Run `flask seed provider` first.")

    created: list[str] = []
    skipped: list[str] = []

    for name in DEMO_ORGS:
        org, made = _get_or_create_org(org_name=name)
        (created if made else skipped).append(f"org {org.name} (demo)")

        handle = org.name.replace(" ", "").lower()
        for role in (ROLE_ADMIN, ROLE_ANALYST):
            email = f"{role}@{handle}.example"
            _, made = _get_or_create_user(email=email, org=org, role=role, password=password)
            (created if made else skipped).append(f"user {email.lower()} ({role})")

    db.session.commit()
    _report(created, skipped)


def register_cli(app: Flask) -> None:
    app.cli.add_command(seed_cli)


def _require_non_prod() -> None:
    if current_app.config.get("CONFIG_NAME") == "prod":
        raise click.ClickException("Database is in production: refusing to write seed data.")


def _get_or_create_org(org_name: str, *, is_provider: bool = False) -> tuple[Organization, bool]:
    org = db.session.scalar(db.select(Organization).filter_by(name=org_name))
    if org is not None:
        return org, False
    org = Organization(name=org_name, is_provider=is_provider)
    db.session.add(org)
    # Flush in order to have Postgres assign org.id
    db.session.flush()
    return org, True


def _get_or_create_user(
        email: str, *, org: Organization, role: str, password: str
) -> tuple[User, bool]:
    email = email.strip().lower()
    user = db.session.scalar(db.select(User).filter_by(email=email))
    if user is not None:
        return user, False
    user = User(
        email=email,
        org_id=org.id,
        role=role,
        password_hash=hash_password(password),
    )
    db.session.add(user)
    return user, True


def _report(created: list[str], skipped: list[str]) -> None:
    for label in created:
        click.echo(f"created {label}")
    for label in skipped:
        click.echo(f"exists {label}")
    click.echo(f"{len(created)} created, {len(skipped)} already existed.")
