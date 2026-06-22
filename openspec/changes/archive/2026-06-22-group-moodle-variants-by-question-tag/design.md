## Context

`generate_moodle_xml()` currently maintains a global `question_number` and uses
it for both the exported question name and Moodle tag. That counter identifies
an individual generated XML question, not the source question position.
`QuestionPool.order` already provides the stable identity required for
grouping all alternatives for one exam question.

## Goals / Non-Goals

**Goals:**

- Use `q{pool.order}` for every variant produced from a question pool.
- Cover multiple versions, multiple templates, and multiple pools.
- Preserve globally sequential question names.

**Non-Goals:**

- Change variant generation, pool ordering, or question naming.
- Change models, migrations, views, URLs, templates, or dependencies.

## Decisions

### 1. Derive the tag directly from QuestionPool.order

While iterating a pool, assign `tag_text.text = f"q{pool.order}"`. Continue
using `question_number` for `<name><text>Q...</text></name>` and increment it
for each generated XML question.

This directly represents domain identity and avoids introducing another
counter or grouping pass.

**Alternatives considered:**

- Reset a tag counter per pool: rejected because `pool.order` is already the
  canonical question position.
- Use the first generated variant's global number for subsequent variants:
  rejected because it is indirect and can diverge from the configured pool
  order.

### 2. Parse XML in regression tests

Tests will extract each question's name and tag using
`xml.etree.ElementTree`, then compare complete ordered sequences. This avoids
false positives from substring assertions.

### 3. No Django or frontend surface changes

There are no database schema, model field, or relationship changes. The
existing `/exams/<uuid:pk>/export/` route remains unchanged. No templates,
inheritance hierarchy, template tags, filters, or static files are involved.

## Risks / Trade-offs

- Non-contiguous custom pool orders produce matching non-contiguous tags, which
  is intentional because the tag reflects configured question identity.
- Question names and tags will no longer necessarily share the same number
  after the first multi-variant pool. This distinction is required: names
  identify exported records, while tags group records by source question.
