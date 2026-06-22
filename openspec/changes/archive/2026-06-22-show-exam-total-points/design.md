## Context

`ExamDetailView` already loads all pools for the template. Each pool has a
`DecimalField(max_digits=5, decimal_places=2)` named `default_grade`.

## Goals / Non-Goals

**Goals:**

- Show an exact decimal sum of pool grades.
- Count each pool once.
- Handle exams without pools.

**Non-Goals:**

- Store a denormalized total on `Exam`.
- Multiply points by templates or versions.
- Change Moodle export grading.

## Decisions

### 1. Aggregate points in ExamDetailView

Use Django ORM `Sum("default_grade")` on the exam's pool relation and default
to `Decimal("0.00")` when the aggregate is `None`. Add the result to context as
`total_points`.

**Alternatives considered:**

- Sum in the template: rejected because Django templates should not perform
  aggregation logic.
- Add an Exam field: rejected because the value is derived and would risk
  becoming stale.

### 2. Display in the Questions card header

Add a primary badge beside the Questions heading in
`apps/exams/templates/exams/exam_detail.html`. Use `floatformat:2` for a stable
two-decimal display.

### 3. No schema or frontend asset changes

There are no models, fields, relationships, migrations, URLs, forms, template
tags, filters, CSS, or JavaScript changes.

## Risks / Trade-offs

- The aggregate adds one inexpensive database query to the detail page.
- The display always uses two decimal places for consistency with the model
  field, even for whole-number totals.
