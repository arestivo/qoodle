"""Management command to import questions from YAML files."""

import re
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.questions.models import Choice, QuestionTemplate
from apps.subjects.models import Subject


class Command(BaseCommand):
    """Import question templates from YAML files with multilingual support."""

    help = "Import questions from a folder containing en/ and pt/ subdirectories with YAML files"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "folder",
            type=str,
            help="Path to folder containing en/ and pt/ subdirectories with YAML files",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse files without creating database records",
        )

    def handle(self, *args, **options):
        """Execute the import command."""
        folder_path = Path(options["folder"])
        dry_run = options["dry_run"]

        # Validate folder structure
        self.validate_folder_structure(folder_path)

        # Get or create Uncategorized subject
        uncategorized_subject = self.get_uncategorized_subject()

        # Discover YAML files
        en_files, pt_files = self.discover_yaml_files(folder_path)

        # Validate matching files
        self.validate_matching_files(en_files, pt_files)

        # Import statistics
        stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "choices_created": 0,
            "language_independent": 0,
            "language_specific": 0,
            "errors": [],
        }

        # Process each file pair
        for filename in sorted(en_files.keys()):
            self.stdout.write(f"\nProcessing: {filename}")

            try:
                # Parse both language versions
                en_data = self.parse_yaml_file(en_files[filename])
                pt_data = self.parse_yaml_file(pt_files[filename])

                # Convert and create question
                if not dry_run:
                    with transaction.atomic():
                        template, choices_count, lang_stats = self.create_question(filename, en_data, pt_data, uncategorized_subject)
                        stats["choices_created"] += choices_count
                        stats["language_independent"] += lang_stats["independent"]
                        stats["language_specific"] += lang_stats["specific"]
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Created: {template.title}"))
                else:
                    self.stdout.write(self.style.WARNING(f"  [DRY RUN] Would create question from {filename}"))

                stats["successful"] += 1

            except Exception as e:
                stats["failed"] += 1
                error_msg = f"{filename}: {str(e)}"
                stats["errors"].append(error_msg)
                self.stdout.write(self.style.ERROR(f"  ✗ Failed: {error_msg}"))

            stats["processed"] += 1

        # Print summary
        self.print_summary(stats, dry_run)

    def validate_folder_structure(self, folder_path: Path):
        """Validate that folder exists and has required subdirectories."""
        if not folder_path.exists():
            raise CommandError(f"Folder does not exist: {folder_path}")

        if not folder_path.is_dir():
            raise CommandError(f"Path is not a directory: {folder_path}")

        en_dir = folder_path / "en"
        pt_dir = folder_path / "pt"

        if not en_dir.exists() or not en_dir.is_dir():
            raise CommandError(f"Missing 'en' subdirectory in {folder_path}")

        if not pt_dir.exists() or not pt_dir.is_dir():
            raise CommandError(f"Missing 'pt' subdirectory in {folder_path}")

        self.stdout.write(self.style.SUCCESS(f"✓ Validated folder structure: {folder_path}"))

    def get_uncategorized_subject(self) -> Subject:
        """Get or create the Uncategorized root subject."""
        subject, created = Subject.objects.get_or_create(
            name="Uncategorized",
            parent=None,
            defaults={"description": "Imported questions to be categorized"},
        )

        if created:
            self.stdout.write(self.style.SUCCESS("✓ Created 'Uncategorized' subject"))
        else:
            self.stdout.write(self.style.SUCCESS("✓ Using existing 'Uncategorized' subject"))

        return subject

    def discover_yaml_files(self, folder_path: Path) -> tuple[dict, dict]:
        """Discover all YAML files in en/ and pt/ subdirectories."""
        en_dir = folder_path / "en"
        pt_dir = folder_path / "pt"

        en_files = {}
        pt_files = {}

        # Find all .yaml and .yml files in en/
        for ext in ["*.yaml", "*.yml"]:
            for file_path in en_dir.glob(ext):
                en_files[file_path.name] = file_path

        # Find all .yaml and .yml files in pt/
        for ext in ["*.yaml", "*.yml"]:
            for file_path in pt_dir.glob(ext):
                pt_files[file_path.name] = file_path

        self.stdout.write(f"Found {len(en_files)} English files and {len(pt_files)} Portuguese files")

        return en_files, pt_files

    def validate_matching_files(self, en_files: dict, pt_files: dict):
        """Validate that each English file has a matching Portuguese file."""
        en_only = set(en_files.keys()) - set(pt_files.keys())
        pt_only = set(pt_files.keys()) - set(en_files.keys())

        if en_only:
            self.stdout.write(self.style.WARNING(f"Warning: English files without Portuguese version: {sorted(en_only)}"))

        if pt_only:
            self.stdout.write(self.style.WARNING(f"Warning: Portuguese files without English version: {sorted(pt_only)}"))

        # Only process files that exist in both languages
        common_files = set(en_files.keys()) & set(pt_files.keys())
        if not common_files:
            raise CommandError("No matching file pairs found")

        # Remove non-matching files from dictionaries
        for filename in list(en_files.keys()):
            if filename not in common_files:
                del en_files[filename]

        for filename in list(pt_files.keys()):
            if filename not in common_files:
                del pt_files[filename]

        self.stdout.write(self.style.SUCCESS(f"✓ Found {len(common_files)} matching file pairs"))

    def parse_yaml_file(self, file_path: Path) -> dict:
        """Parse a YAML file and return the data."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise ValueError("YAML file must contain a dictionary")

            return data

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

    def convert_variables(self, yaml_vars: dict) -> dict:
        """
        Convert YAML variable definitions to model format.

        Converts:
        - 'type: number' to 'type: num'
        - 'type: expr' to 'type: expression'
        - 'values' key to 'items' for set type
        - Validates structure matches model requirements
        """
        if not yaml_vars:
            return {}

        converted = {}

        for var_name, var_def in yaml_vars.items():
            if not isinstance(var_def, dict):
                raise ValueError(f"Variable '{var_name}' must be a dictionary")

            var_type = var_def.get("type")

            # Convert 'number' to 'num' (YAML uses 'number', model uses 'num')
            if var_type == "number":
                var_def = dict(var_def)  # Make a copy
                var_def["type"] = "num"
                var_type = "num"

            # Convert 'expr' to 'expression' and strip angle brackets from formula
            if var_type == "expr" or var_type == "expression":
                var_def = dict(var_def)  # Make a copy
                var_def["type"] = "expression"
                # Convert <var> to var in formula (Python eval uses bare variable names)
                if "formula" in var_def:
                    formula = str(var_def["formula"])
                    formula = formula.replace("<", "").replace(">", "")
                    var_def["formula"] = formula
                var_type = "expression"

            if var_type == "set":
                # Convert 'values' to 'items'
                if "values" in var_def:
                    converted[var_name] = {
                        "type": "set",
                        "items": var_def["values"],
                        "size": var_def.get("size", 1),
                    }
                elif "items" in var_def:
                    # Already in correct format
                    converted[var_name] = var_def
                else:
                    raise ValueError(f"Set variable '{var_name}' missing 'values' or 'items' field")

            else:
                # Other types (num, string, expression) - pass through
                converted[var_name] = var_def

        return converted

    def convert_text_references(self, text: str) -> str:
        """
        Convert variable references from <var> to {{var}} syntax.

        Examples:
        - <c[0]> -> {{c[0]}}
        - <w[1]> -> {{w[1]}}
        - <x> -> {{x}}
        """
        if not text:
            return text

        # Pattern to match <...> with content inside
        pattern = r"<([^>]+)>"

        def replace_brackets(match):
            content = match.group(1)
            return f"{{{{{content}}}}}"

        return re.sub(pattern, replace_brackets, text)

    def create_multilingual_text(self, en_text: str, pt_text: str) -> tuple[dict, str]:
        """
        Create multilingual text structure.

        Returns:
        - dict: Multilingual text in model format
        - str: "independent" or "specific"
        """
        # Convert variable references
        en_converted = self.convert_text_references(en_text)
        pt_converted = self.convert_text_references(pt_text)

        # Compare converted texts
        if en_converted == pt_converted:
            # Language-independent
            return {"none": en_converted}, "independent"
        else:
            # Language-specific
            return {"en": en_converted, "pt": pt_converted}, "specific"

    def derive_title_from_filename(self, filename: str) -> str:
        """
        Derive a human-readable title from filename.

        Example: "spa-advantage.yaml" -> "Spa Advantage"
        """
        # Remove extension
        name = Path(filename).stem

        # Replace hyphens and underscores with spaces
        name = name.replace("-", " ").replace("_", " ")

        # Title case
        return name.title()

    def create_question(
        self,
        filename: str,
        en_data: dict,
        pt_data: dict,
        subject: Subject,
    ) -> tuple[QuestionTemplate, int, dict]:
        """
        Create QuestionTemplate and Choice objects from parsed data.

        Returns:
        - QuestionTemplate: Created template
        - int: Number of choices created
        - dict: Language statistics
        """
        # Derive title
        title = self.derive_title_from_filename(filename)

        # Convert variables
        variables = self.convert_variables(en_data.get("vars", {}))

        # Create multilingual question text
        en_question_text = en_data.get("text", "").strip()
        pt_question_text = pt_data.get("text", "").strip()

        if not en_question_text or not pt_question_text:
            raise ValueError("Question text is required in both languages")

        question_text, text_type = self.create_multilingual_text(en_question_text, pt_question_text)

        # Track language statistics
        lang_stats = {"independent": 0, "specific": 0}
        lang_stats[text_type] += 1

        # Create QuestionTemplate
        template = QuestionTemplate.objects.create(
            subject=subject,
            title=title,
            text=question_text,
            variables=variables,
        )

        # Create choices
        en_choices = en_data.get("choices", [])
        pt_choices = pt_data.get("choices", [])

        if len(en_choices) != len(pt_choices):
            raise ValueError(f"Mismatch in number of choices: {len(en_choices)} (en) vs {len(pt_choices)} (pt)")

        if not en_choices:
            raise ValueError("At least one choice is required")

        choices_created = 0
        for order, (en_choice, pt_choice) in enumerate(zip(en_choices, pt_choices)):
            # Convert choice text
            en_choice_text = str(en_choice).strip()
            pt_choice_text = str(pt_choice).strip()

            if not en_choice_text or not pt_choice_text:
                raise ValueError(f"Choice {order} text is empty")

            choice_text, choice_text_type = self.create_multilingual_text(en_choice_text, pt_choice_text)
            lang_stats[choice_text_type] += 1

            # Create Choice
            Choice.objects.create(
                template=template,
                text=choice_text,
                order=order,
            )

            choices_created += 1

        return template, choices_created, lang_stats

    def print_summary(self, stats: dict, dry_run: bool):
        """Print import summary statistics."""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("IMPORT SUMMARY" + (" (DRY RUN)" if dry_run else "")))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Files processed:     {stats['processed']}")
        self.stdout.write(self.style.SUCCESS(f"Successful:          {stats['successful']}"))

        if stats["failed"] > 0:
            self.stdout.write(self.style.ERROR(f"Failed:              {stats['failed']}"))

        if not dry_run:
            self.stdout.write(f"Choices created:     {stats['choices_created']}")
            self.stdout.write(f"Language-independent texts: {stats['language_independent']}")
            self.stdout.write(f"Language-specific texts:    {stats['language_specific']}")

        if stats["errors"]:
            self.stdout.write("\n" + self.style.ERROR("ERRORS:"))
            for error in stats["errors"]:
                self.stdout.write(self.style.ERROR(f"  • {error}"))

        self.stdout.write("=" * 60)
