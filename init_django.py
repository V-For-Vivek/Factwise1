import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import django


def setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "factwise_project.settings")
    if not django.apps.apps.ready:  # type: ignore
        django.setup()

    try:
        from django.db import connection

        tables = connection.introspection.table_names()
        if "planner_usermodel" not in tables:
            from django.core.management import call_command

            call_command("migrate", interactive=False, verbosity=0)
    except Exception:
        from django.core.management import call_command

        call_command("migrate", interactive=False, verbosity=0)


setup_django()
