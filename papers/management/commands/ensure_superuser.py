"""Create the initial Django administrator from environment variables, once."""
from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Idempotently create the initial superuser from DJANGO_SUPERUSER_* variables."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        configured = [value for value in (username, email, password) if value]
        if not configured:
            self.stdout.write("No superuser environment variables configured; skipping initialization.")
            return
        if not all((username, email, password)):
            raise CommandError("DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and DJANGO_SUPERUSER_PASSWORD must all be set together.")

        user_model = get_user_model()
        identity_field = user_model.USERNAME_FIELD
        identity_value = email if identity_field == "email" else username
        manager = user_model._default_manager
        if manager.filter(**{identity_field: identity_value}).exists():
            self.stdout.write("Initial superuser already exists; skipping initialization.")
            return

        fields = {field.name: field for field in user_model._meta.fields}
        extra_fields: dict[str, str] = {}
        if "email" in fields and identity_field != "email":
            extra_fields["email"] = email
        missing_required = [field.name for field in fields.values() if not field.blank and not field.null and not field.has_default() and not field.primary_key and not field.auto_created and field.name not in {identity_field, "password"} and field.name not in extra_fields and field.name not in {"is_staff", "is_superuser", "is_active", "last_login", "date_joined"}]
        if missing_required:
            raise CommandError(f"Cannot initialize superuser: required user fields need values: {', '.join(missing_required)}")
        user_model._default_manager.create_superuser(**{identity_field: identity_value, "password": password, **extra_fields})
        self.stdout.write("Initial superuser created successfully.")
