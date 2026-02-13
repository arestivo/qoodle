"""Shared export/import logic for application data backup."""

from __future__ import annotations

import uuid
from collections import deque
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from django.utils import timezone

from apps.exams.models import Exam, QuestionPool, QuestionPoolTemplate
from apps.questions.models import Choice, QuestionTemplate
from apps.subjects.models import Subject


FORMAT_VERSION = 1


def _serialize_value(value: Any) -> Any:
    """Serialize a single field value to JSON-safe format."""
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _serialize_subject(subject: Subject) -> dict:
    """Serialize a Subject instance to a dictionary."""
    return {
        "id": str(subject.id),
        "name": subject.name,
        "parent": str(subject.parent_id) if subject.parent_id else None,
        "description": subject.description,
        "created_at": subject.created_at.isoformat(),
        "updated_at": subject.updated_at.isoformat(),
    }


def _serialize_template(template: QuestionTemplate) -> dict:
    """Serialize a QuestionTemplate instance to a dictionary."""
    return {
        "id": str(template.id),
        "subject": str(template.subject_id),
        "title": template.title,
        "text": template.text,
        "variables": template.variables,
        "validation_rules": template.validation_rules,
        "tags": template.tags,
        "state": template.state,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat(),
    }


def _serialize_choice(choice: Choice) -> dict:
    """Serialize a Choice instance to a dictionary."""
    return {
        "id": str(choice.id),
        "template": str(choice.template_id),
        "text": choice.text,
        "order": choice.order,
        "created_at": choice.created_at.isoformat(),
        "updated_at": choice.updated_at.isoformat(),
    }


def _serialize_exam(exam: Exam) -> dict:
    """Serialize an Exam instance to a dictionary."""
    return {
        "id": str(exam.id),
        "title": exam.title,
        "date": exam.date.isoformat() if exam.date else None,
        "description": exam.description,
        "grading_mode": exam.grading_mode,
        "created_at": exam.created_at.isoformat(),
        "updated_at": exam.updated_at.isoformat(),
    }


def _serialize_pool(pool: QuestionPool) -> dict:
    """Serialize a QuestionPool instance to a dictionary."""
    return {
        "id": str(pool.id),
        "exam": str(pool.exam_id),
        "order": pool.order,
        "default_grade": str(pool.default_grade),
        "created_at": pool.created_at.isoformat(),
        "updated_at": pool.updated_at.isoformat(),
    }


def _serialize_pool_template(pt: QuestionPoolTemplate) -> dict:
    """Serialize a QuestionPoolTemplate instance to a dictionary."""
    return {
        "id": str(pt.id),
        "pool": str(pt.pool_id),
        "template": str(pt.template_id),
        "number_of_versions": pt.number_of_versions,
        "created_at": pt.created_at.isoformat(),
        "updated_at": pt.updated_at.isoformat(),
    }


def _topological_sort_subjects(subjects: list[Subject]) -> list[Subject]:
    """Sort subjects so parents come before children."""
    by_id = {s.id: s for s in subjects}
    children: dict[uuid.UUID | None, list[Subject]] = {}
    for s in subjects:
        children.setdefault(s.parent_id, []).append(s)

    result: list[Subject] = []
    queue: deque[uuid.UUID | None] = deque([None])
    while queue:
        parent_id = queue.popleft()
        for child in children.get(parent_id, []):
            result.append(child)
            queue.append(child.id)
    return result


def export_data() -> dict:
    """Serialize all application data to a dictionary."""
    subjects = _topological_sort_subjects(list(Subject.objects.all()))
    templates = list(QuestionTemplate.objects.all().order_by("title"))
    choices = list(Choice.objects.all().order_by("template_id", "order"))
    exams = list(Exam.objects.all().order_by("title"))
    pools = list(QuestionPool.objects.all().order_by("exam_id", "order"))
    pool_templates = list(
        QuestionPoolTemplate.objects.all().order_by("pool_id", "template_id")
    )

    return {
        "version": FORMAT_VERSION,
        "exported_at": timezone.now().isoformat(),
        "subjects": [_serialize_subject(s) for s in subjects],
        "templates": [_serialize_template(t) for t in templates],
        "choices": [_serialize_choice(c) for c in choices],
        "exams": [_serialize_exam(e) for e in exams],
        "pools": [_serialize_pool(p) for p in pools],
        "pool_templates": [_serialize_pool_template(pt) for pt in pool_templates],
    }


def get_existing_data_counts() -> dict[str, int]:
    """Return counts of existing records per model type."""
    return {
        "subjects": Subject.objects.count(),
        "templates": QuestionTemplate.objects.count(),
        "choices": Choice.objects.count(),
        "exams": Exam.objects.count(),
        "pools": QuestionPool.objects.count(),
        "pool_templates": QuestionPoolTemplate.objects.count(),
    }


def has_existing_data() -> bool:
    """Check if any application data exists in the database."""
    counts = get_existing_data_counts()
    return any(v > 0 for v in counts.values())


def delete_all_data() -> None:
    """Delete all application data in reverse dependency order."""
    QuestionPoolTemplate.objects.all().delete()
    QuestionPool.objects.all().delete()
    Exam.objects.all().delete()
    Choice.objects.all().delete()
    QuestionTemplate.objects.all().delete()
    # Delete subjects children-first (PROTECT on parent FK)
    while Subject.objects.exists():
        leaf_ids = Subject.objects.filter(children__isnull=True).values_list("id", flat=True)
        Subject.objects.filter(id__in=list(leaf_ids)).delete()


def _parse_datetime(value: str) -> datetime:
    """Parse an ISO 8601 datetime string."""
    return datetime.fromisoformat(value)


def _parse_date(value: str | None) -> date | None:
    """Parse an ISO 8601 date string or return None."""
    if value is None:
        return None
    return date.fromisoformat(value)


def _import_subjects(subjects_data: list[dict]) -> int:
    """Import subjects in topological order (parents first)."""
    # Build a map of id -> data for ordering
    by_id = {s["id"]: s for s in subjects_data}

    # Topological sort: parents before children
    children_map: dict[str | None, list[dict]] = {}
    for s in subjects_data:
        children_map.setdefault(s["parent"], []).append(s)

    ordered: list[dict] = []
    queue: deque[str | None] = deque([None])
    while queue:
        parent_id = queue.popleft()
        for child in children_map.get(parent_id, []):
            ordered.append(child)
            queue.append(child["id"])

    for s in ordered:
        Subject.objects.create(
            id=uuid.UUID(s["id"]),
            name=s["name"],
            parent_id=uuid.UUID(s["parent"]) if s["parent"] else None,
            description=s.get("description", ""),
        )
        # Restore timestamps (auto_now_add/auto_now prevent direct setting)
        Subject.objects.filter(pk=uuid.UUID(s["id"])).update(
            created_at=_parse_datetime(s["created_at"]),
            updated_at=_parse_datetime(s["updated_at"]),
        )
    return len(ordered)


def _import_templates(templates_data: list[dict]) -> int:
    """Import question templates."""
    for t in templates_data:
        QuestionTemplate.objects.create(
            id=uuid.UUID(t["id"]),
            subject_id=uuid.UUID(t["subject"]),
            title=t["title"],
            text=t["text"],
            variables=t.get("variables") or {},
            validation_rules=t.get("validation_rules") or [],
            tags=t.get("tags", ""),
            state=t.get("state", "draft"),
        )
        QuestionTemplate.objects.filter(pk=uuid.UUID(t["id"])).update(
            created_at=_parse_datetime(t["created_at"]),
            updated_at=_parse_datetime(t["updated_at"]),
        )
    return len(templates_data)


def _import_choices(choices_data: list[dict]) -> int:
    """Import choices."""
    for c in choices_data:
        Choice.objects.create(
            id=uuid.UUID(c["id"]),
            template_id=uuid.UUID(c["template"]),
            text=c["text"],
            order=c["order"],
        )
        Choice.objects.filter(pk=uuid.UUID(c["id"])).update(
            created_at=_parse_datetime(c["created_at"]),
            updated_at=_parse_datetime(c["updated_at"]),
        )
    return len(choices_data)


def _import_exams(exams_data: list[dict]) -> int:
    """Import exams."""
    for e in exams_data:
        Exam.objects.create(
            id=uuid.UUID(e["id"]),
            title=e["title"],
            date=_parse_date(e.get("date")),
            description=e.get("description", ""),
            grading_mode=e.get("grading_mode", "single"),
        )
        Exam.objects.filter(pk=uuid.UUID(e["id"])).update(
            created_at=_parse_datetime(e["created_at"]),
            updated_at=_parse_datetime(e["updated_at"]),
        )
    return len(exams_data)


def _import_pools(pools_data: list[dict]) -> int:
    """Import question pools."""
    for p in pools_data:
        QuestionPool.objects.create(
            id=uuid.UUID(p["id"]),
            exam_id=uuid.UUID(p["exam"]),
            order=p["order"],
            default_grade=Decimal(p["default_grade"]),
        )
        QuestionPool.objects.filter(pk=uuid.UUID(p["id"])).update(
            created_at=_parse_datetime(p["created_at"]),
            updated_at=_parse_datetime(p["updated_at"]),
        )
    return len(pools_data)


def _import_pool_templates(pool_templates_data: list[dict]) -> int:
    """Import question pool templates."""
    for pt in pool_templates_data:
        QuestionPoolTemplate.objects.create(
            id=uuid.UUID(pt["id"]),
            pool_id=uuid.UUID(pt["pool"]),
            template_id=uuid.UUID(pt["template"]),
            number_of_versions=pt["number_of_versions"],
        )
        QuestionPoolTemplate.objects.filter(pk=uuid.UUID(pt["id"])).update(
            created_at=_parse_datetime(pt["created_at"]),
            updated_at=_parse_datetime(pt["updated_at"]),
        )
    return len(pool_templates_data)


def import_data(data: dict) -> dict[str, int]:
    """Import data from a dictionary. Returns counts of imported records.

    Caller is responsible for wrapping in transaction.atomic() and
    deleting existing data before calling this.
    """
    version = data.get("version")
    if version != FORMAT_VERSION:
        raise ValueError(
            f"Unsupported format version: {version}. Expected {FORMAT_VERSION}."
        )

    counts = {
        "subjects": _import_subjects(data.get("subjects", [])),
        "templates": _import_templates(data.get("templates", [])),
        "choices": _import_choices(data.get("choices", [])),
        "exams": _import_exams(data.get("exams", [])),
        "pools": _import_pools(data.get("pools", [])),
        "pool_templates": _import_pool_templates(data.get("pool_templates", [])),
    }
    return counts
