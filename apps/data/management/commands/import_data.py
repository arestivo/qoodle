"""Management command to import application data from a JSON file."""

import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.data.services import (
    delete_all_data,
    get_existing_data_counts,
    has_existing_data,
    import_data,
)


class Command(BaseCommand):
    """Import application data from a JSON file."""

    help = "Import application data from a JSON file (destructive replace)"

    def add_arguments(self, parser):
        parser.add_argument(
            "input_path",
            type=str,
            help="File path to read the JSON import from",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skip the non-empty database warning and proceed with destructive import",
        )

    def handle(self, *args, **options):
        input_path = options["input_path"]
        force = options["force"]

        # Read and parse JSON file
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"File not found: {input_path}")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON file: {e}")

        # Check for existing data
        if has_existing_data() and not force:
            counts = get_existing_data_counts()
            self.stdout.write(self.style.WARNING("Database contains existing data:"))
            for model_name, count in counts.items():
                if count > 0:
                    self.stdout.write(f"  {model_name}: {count}")
            self.stdout.write(
                self.style.WARNING(
                    "\nAll existing data will be deleted. "
                    "Use --force to proceed."
                )
            )
            return

        # Perform import inside a transaction
        self.stdout.write("Importing application data...")
        try:
            with transaction.atomic():
                if has_existing_data():
                    self.stdout.write("Deleting existing data...")
                    delete_all_data()
                counts = import_data(data)
        except ValueError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f"Import failed: {e}")

        self.stdout.write(self.style.SUCCESS("Import complete!"))
        for model_name, count in counts.items():
            self.stdout.write(f"  {model_name}: {count}")
