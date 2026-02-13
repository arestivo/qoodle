"""Management command to export all application data to a JSON file."""

import json

from django.core.management.base import BaseCommand

from apps.data.services import export_data


class Command(BaseCommand):
    """Export all application data to a JSON file."""

    help = "Export all application data (subjects, templates, choices, exams) to a JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "output_path",
            type=str,
            help="File path to write the JSON export to",
        )

    def handle(self, *args, **options):
        output_path = options["output_path"]

        self.stdout.write("Exporting application data...")
        data = export_data()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f"Export written to: {output_path}"))
        self.stdout.write(f"  Subjects: {len(data['subjects'])}")
        self.stdout.write(f"  Templates: {len(data['templates'])}")
        self.stdout.write(f"  Choices: {len(data['choices'])}")
        self.stdout.write(f"  Exams: {len(data['exams'])}")
        self.stdout.write(f"  Pools: {len(data['pools'])}")
        self.stdout.write(f"  Pool Templates: {len(data['pool_templates'])}")
