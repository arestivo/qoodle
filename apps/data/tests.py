"""Tests for the data management app."""

import json
import uuid
from decimal import Decimal
from io import BytesIO, StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.data.services import (
    delete_all_data,
    export_data,
    get_existing_data_counts,
    has_existing_data,
    import_data,
)
from apps.exams.models import Exam, QuestionPool, QuestionPoolTemplate
from apps.questions.models import Choice, QuestionTemplate
from apps.subjects.models import Subject


class ExportDataServiceTests(TestCase):
    """Tests for the export_data service function."""

    def test_export_empty_database(self):
        """Exporting an empty database produces valid structure with empty arrays."""
        data = export_data()
        self.assertEqual(data["version"], 1)
        self.assertIn("exported_at", data)
        self.assertEqual(data["subjects"], [])
        self.assertEqual(data["templates"], [])
        self.assertEqual(data["choices"], [])
        self.assertEqual(data["exams"], [])
        self.assertEqual(data["pools"], [])
        self.assertEqual(data["pool_templates"], [])

    def test_export_serializes_all_models(self):
        """Export includes all model types with correct field values."""
        subject = Subject.objects.create(name="Math")
        template = QuestionTemplate.objects.create(
            subject=subject,
            title="Q1",
            text={"none": "What is 1+1?"},
            variables={"x": {"type": "num", "min": 1, "max": 10, "precision": 1}},
            tags="easy,math",
            state="reviewed",
        )
        Choice.objects.create(template=template, text={"none": "2"}, order=0)
        Choice.objects.create(template=template, text={"none": "3"}, order=1)
        exam = Exam.objects.create(title="Midterm", grading_mode="single")
        pool = QuestionPool.objects.create(exam=exam, order=1, default_grade=Decimal("2.5"))
        QuestionPoolTemplate.objects.create(pool=pool, template=template, number_of_versions=3)

        data = export_data()

        self.assertEqual(len(data["subjects"]), 1)
        self.assertEqual(data["subjects"][0]["name"], "Math")
        self.assertEqual(len(data["templates"]), 1)
        self.assertEqual(data["templates"][0]["title"], "Q1")
        self.assertEqual(data["templates"][0]["state"], "reviewed")
        self.assertEqual(data["templates"][0]["tags"], "easy,math")
        self.assertEqual(len(data["choices"]), 2)
        self.assertEqual(len(data["exams"]), 1)
        self.assertEqual(data["exams"][0]["title"], "Midterm")
        self.assertEqual(len(data["pools"]), 1)
        self.assertEqual(data["pools"][0]["default_grade"], "2.50")
        self.assertEqual(len(data["pool_templates"]), 1)
        self.assertEqual(data["pool_templates"][0]["number_of_versions"], 3)

    def test_export_subjects_topological_order(self):
        """Subjects are exported with parents before children."""
        parent = Subject.objects.create(name="Science")
        child = Subject.objects.create(name="Physics", parent=parent)
        grandchild = Subject.objects.create(name="Mechanics", parent=child)

        data = export_data()
        names = [s["name"] for s in data["subjects"]]
        self.assertEqual(names, ["Science", "Physics", "Mechanics"])

    def test_export_preserves_uuids(self):
        """Exported UUIDs match the database UUIDs."""
        subject = Subject.objects.create(name="Math")
        data = export_data()
        self.assertEqual(data["subjects"][0]["id"], str(subject.id))

    def test_export_json_fields_not_double_encoded(self):
        """JSONField values are nested directly, not double-encoded as strings."""
        subject = Subject.objects.create(name="Math")
        template = QuestionTemplate.objects.create(
            subject=subject,
            title="Q1",
            text={"en": "Hello", "pt": "Olá"},
            variables={"x": {"type": "num", "min": 1, "max": 10, "precision": 1}},
            validation_rules=["x > 0"],
        )
        data = export_data()
        t = data["templates"][0]
        self.assertIsInstance(t["text"], dict)
        self.assertIsInstance(t["variables"], dict)
        self.assertIsInstance(t["validation_rules"], list)


class ImportDataServiceTests(TestCase):
    """Tests for the import_data service function."""

    def test_import_into_empty_database(self):
        """Import into empty database creates all records."""
        subject_id = str(uuid.uuid4())
        template_id = str(uuid.uuid4())
        choice_id = str(uuid.uuid4())
        exam_id = str(uuid.uuid4())
        pool_id = str(uuid.uuid4())
        pt_id = str(uuid.uuid4())

        data = {
            "version": 1,
            "exported_at": "2026-01-01T00:00:00+00:00",
            "subjects": [
                {
                    "id": subject_id,
                    "name": "Math",
                    "parent": None,
                    "description": "",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "templates": [
                {
                    "id": template_id,
                    "subject": subject_id,
                    "title": "Q1",
                    "text": {"none": "Question?"},
                    "variables": {},
                    "validation_rules": [],
                    "tags": "",
                    "state": "draft",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "choices": [
                {
                    "id": choice_id,
                    "template": template_id,
                    "text": {"none": "Answer"},
                    "order": 0,
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "exams": [
                {
                    "id": exam_id,
                    "title": "Midterm",
                    "date": None,
                    "description": "",
                    "grading_mode": "single",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "pools": [
                {
                    "id": pool_id,
                    "exam": exam_id,
                    "order": 1,
                    "default_grade": "1.0",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "pool_templates": [
                {
                    "id": pt_id,
                    "pool": pool_id,
                    "template": template_id,
                    "number_of_versions": 1,
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
        }

        counts = import_data(data)

        self.assertEqual(counts["subjects"], 1)
        self.assertEqual(counts["templates"], 1)
        self.assertEqual(counts["choices"], 1)
        self.assertEqual(counts["exams"], 1)
        self.assertEqual(counts["pools"], 1)
        self.assertEqual(counts["pool_templates"], 1)

    def test_import_preserves_uuids(self):
        """Imported records have the same UUIDs as in the export."""
        subject_id = str(uuid.uuid4())
        data = {
            "version": 1,
            "exported_at": "2026-01-01T00:00:00+00:00",
            "subjects": [
                {
                    "id": subject_id,
                    "name": "Math",
                    "parent": None,
                    "description": "",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "templates": [],
            "choices": [],
            "exams": [],
            "pools": [],
            "pool_templates": [],
        }
        import_data(data)
        self.assertTrue(Subject.objects.filter(pk=uuid.UUID(subject_id)).exists())

    def test_import_invalid_version(self):
        """Import with wrong version raises ValueError."""
        data = {"version": 99}
        with self.assertRaises(ValueError):
            import_data(data)

    def test_import_missing_version(self):
        """Import with no version field raises ValueError."""
        data = {"subjects": []}
        with self.assertRaises(ValueError):
            import_data(data)


class RoundTripTests(TestCase):
    """Tests for export/import round-trip consistency."""

    def test_round_trip_preserves_data(self):
        """Exporting then importing produces equivalent data."""
        parent = Subject.objects.create(name="Science")
        child = Subject.objects.create(name="Physics", parent=parent)
        template = QuestionTemplate.objects.create(
            subject=child,
            title="Velocity",
            text={"en": "What is velocity?", "pt": "O que é velocidade?"},
            variables={"v": {"type": "num", "min": 0, "max": 100, "precision": 1}},
            validation_rules=["v > 0"],
            tags="physics,kinematics",
            state="reviewed",
        )
        Choice.objects.create(template=template, text={"en": "speed/time"}, order=0)
        Choice.objects.create(template=template, text={"en": "distance/time"}, order=1)
        exam = Exam.objects.create(title="Physics Exam", date="2026-06-15", grading_mode="multi")
        pool = QuestionPool.objects.create(exam=exam, order=1, default_grade=Decimal("3.0"))
        QuestionPoolTemplate.objects.create(pool=pool, template=template, number_of_versions=5)

        # Export
        data = export_data()

        # Clear DB
        delete_all_data()
        self.assertFalse(has_existing_data())

        # Import
        counts = import_data(data)
        self.assertEqual(counts["subjects"], 2)
        self.assertEqual(counts["templates"], 1)
        self.assertEqual(counts["choices"], 2)
        self.assertEqual(counts["exams"], 1)
        self.assertEqual(counts["pools"], 1)
        self.assertEqual(counts["pool_templates"], 1)

        # Verify data
        self.assertEqual(Subject.objects.count(), 2)
        child_reloaded = Subject.objects.get(name="Physics")
        self.assertEqual(child_reloaded.parent.name, "Science")

        template_reloaded = QuestionTemplate.objects.get(title="Velocity")
        self.assertEqual(template_reloaded.text, {"en": "What is velocity?", "pt": "O que é velocidade?"})
        self.assertEqual(template_reloaded.state, "reviewed")
        self.assertEqual(template_reloaded.tags, "physics,kinematics")

        exam_reloaded = Exam.objects.get(title="Physics Exam")
        self.assertEqual(str(exam_reloaded.date), "2026-06-15")
        self.assertEqual(exam_reloaded.grading_mode, "multi")

        pool_reloaded = QuestionPool.objects.get(exam=exam_reloaded)
        self.assertEqual(pool_reloaded.default_grade, Decimal("3.0"))

        pt_reloaded = QuestionPoolTemplate.objects.get(pool=pool_reloaded)
        self.assertEqual(pt_reloaded.number_of_versions, 5)
        self.assertEqual(pt_reloaded.template.title, "Velocity")


class HelperFunctionTests(TestCase):
    """Tests for helper functions."""

    def test_get_existing_data_counts_empty(self):
        """Empty database returns all zeros."""
        counts = get_existing_data_counts()
        self.assertEqual(sum(counts.values()), 0)

    def test_has_existing_data_false(self):
        """Empty database returns False."""
        self.assertFalse(has_existing_data())

    def test_has_existing_data_true(self):
        """Database with subjects returns True."""
        Subject.objects.create(name="Math")
        self.assertTrue(has_existing_data())

    def test_delete_all_data(self):
        """delete_all_data removes everything."""
        subject = Subject.objects.create(name="Math")
        QuestionTemplate.objects.create(
            subject=subject, title="Q1", text={"none": "Q?"}
        )
        delete_all_data()
        self.assertFalse(has_existing_data())


class ExportCommandTests(TestCase):
    """Tests for the export_data management command."""

    def test_export_command_writes_file(self):
        """Command writes valid JSON to the specified path."""
        import tempfile
        import os

        Subject.objects.create(name="Math")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            out = StringIO()
            call_command("export_data", path, stdout=out)

            with open(path, "r") as f:
                data = json.load(f)

            self.assertEqual(data["version"], 1)
            self.assertEqual(len(data["subjects"]), 1)
            self.assertIn("Subjects: 1", out.getvalue())
        finally:
            os.unlink(path)


class ImportCommandTests(TestCase):
    """Tests for the import_data management command."""

    def _write_json_file(self, data: dict) -> str:
        """Write data to a temp JSON file and return path."""
        import tempfile

        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump(data, f, ensure_ascii=False)
        f.close()
        return f.name

    def _make_valid_data(self) -> dict:
        """Create minimal valid import data."""
        return {
            "version": 1,
            "exported_at": "2026-01-01T00:00:00+00:00",
            "subjects": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Math",
                    "parent": None,
                    "description": "",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "templates": [],
            "choices": [],
            "exams": [],
            "pools": [],
            "pool_templates": [],
        }

    def test_import_into_empty_db(self):
        """Import into empty database succeeds."""
        import os

        data = self._make_valid_data()
        path = self._write_json_file(data)

        try:
            out = StringIO()
            call_command("import_data", path, stdout=out)
            self.assertEqual(Subject.objects.count(), 1)
            self.assertIn("Import complete", out.getvalue())
        finally:
            os.unlink(path)

    def test_import_non_empty_db_no_force(self):
        """Import into non-empty database without --force shows warning."""
        import os

        Subject.objects.create(name="Existing")
        data = self._make_valid_data()
        path = self._write_json_file(data)

        try:
            out = StringIO()
            call_command("import_data", path, stdout=out)
            output = out.getvalue()
            self.assertIn("existing data", output.lower())
            self.assertIn("--force", output)
            # Original data should still be there
            self.assertEqual(Subject.objects.count(), 1)
            self.assertEqual(Subject.objects.first().name, "Existing")
        finally:
            os.unlink(path)

    def test_import_non_empty_db_with_force(self):
        """Import into non-empty database with --force replaces data."""
        import os

        Subject.objects.create(name="Existing")
        data = self._make_valid_data()
        path = self._write_json_file(data)

        try:
            out = StringIO()
            call_command("import_data", path, "--force", stdout=out)
            self.assertEqual(Subject.objects.count(), 1)
            self.assertEqual(Subject.objects.first().name, "Math")
        finally:
            os.unlink(path)

    def test_import_invalid_json(self):
        """Import with invalid JSON raises CommandError."""
        import os
        import tempfile

        from django.core.management.base import CommandError

        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        f.write("not valid json {{{")
        f.close()

        try:
            with self.assertRaises(CommandError):
                call_command("import_data", f.name)
        finally:
            os.unlink(f.name)


class WebExportViewTests(TestCase):
    """Tests for the web export view."""

    def test_export_download(self):
        """GET /data/export/ returns JSON file download."""
        Subject.objects.create(name="Math")
        response = self.client.get(reverse("data:export"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn("qoodle-export-", response["Content-Disposition"])

        data = json.loads(response.content)
        self.assertEqual(data["version"], 1)
        self.assertEqual(len(data["subjects"]), 1)


class WebImportViewTests(TestCase):
    """Tests for the web import view."""

    def _make_upload_file(self, data: dict) -> BytesIO:
        """Create an in-memory file for upload."""
        content = json.dumps(data).encode("utf-8")
        f = BytesIO(content)
        f.name = "backup.json"
        return f

    def _make_valid_data(self) -> dict:
        """Create minimal valid import data."""
        return {
            "version": 1,
            "exported_at": "2026-01-01T00:00:00+00:00",
            "subjects": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Imported",
                    "parent": None,
                    "description": "",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "templates": [],
            "choices": [],
            "exams": [],
            "pools": [],
            "pool_templates": [],
        }

    def test_import_into_empty_db_redirects(self):
        """Import into empty database imports and redirects."""
        data = self._make_valid_data()
        f = self._make_upload_file(data)
        response = self.client.post(reverse("data:import"), {"file": f})
        self.assertRedirects(response, reverse("data:index"))
        self.assertEqual(Subject.objects.count(), 1)
        self.assertEqual(Subject.objects.first().name, "Imported")

    def test_import_into_non_empty_db_shows_confirmation(self):
        """Import into non-empty database shows confirmation page."""
        Subject.objects.create(name="Existing")
        data = self._make_valid_data()
        f = self._make_upload_file(data)
        response = self.client.post(reverse("data:import"), {"file": f})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Confirm")
        self.assertContains(response, "subjects")
        # Original data should still be there
        self.assertEqual(Subject.objects.first().name, "Existing")

    def test_import_confirmation_completes(self):
        """Confirming import replaces existing data."""
        Subject.objects.create(name="Existing")
        data = self._make_valid_data()

        # First POST to store data in session
        f = self._make_upload_file(data)
        self.client.post(reverse("data:import"), {"file": f})

        # Confirm POST
        response = self.client.post(reverse("data:import"), {"confirm": "true"})
        self.assertRedirects(response, reverse("data:index"))
        self.assertEqual(Subject.objects.count(), 1)
        self.assertEqual(Subject.objects.first().name, "Imported")

    def test_import_invalid_json_shows_error(self):
        """Upload of non-JSON file shows error and redirects."""
        f = BytesIO(b"not json")
        f.name = "bad.json"
        response = self.client.post(reverse("data:import"), {"file": f})
        self.assertRedirects(response, reverse("data:index"))
        self.assertEqual(Subject.objects.count(), 0)

    def test_get_import_redirects(self):
        """GET on import URL redirects to index."""
        response = self.client.get(reverse("data:import"))
        self.assertRedirects(response, reverse("data:index"))

    def test_index_page_loads(self):
        """Data index page loads successfully."""
        response = self.client.get(reverse("data:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Export")
        self.assertContains(response, "Import")
