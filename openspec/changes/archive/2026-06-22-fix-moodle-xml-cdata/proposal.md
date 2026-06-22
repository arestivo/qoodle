## Why

Moodle XML exports currently place literal `<![CDATA[...]]>` marker strings into
`xml.etree.ElementTree` text nodes. ElementTree escapes those markers, producing
`&lt;![CDATA[` and `]]&gt;` in the downloaded file instead of actual CDATA
sections. This violates the existing Moodle XML export specification and can
prevent HTML question and answer content from being interpreted correctly by
Moodle.

## Context

This corrects the existing Moodle XML export pipeline in
`apps/exams/moodle_export.py`. It retains the established multilingual text
selection, variable substitution, Markdown conversion, grading, and Moodle 4.x
structure. The project already depends on Python's standard-library XML modules
and `markdown`; `pyproject.toml` confirms that no new dependency is required.

## What Changes

- Serialize question and answer HTML as real XML CDATA nodes.
- Keep CDATA terminator protection for user-authored content.
- Replace the regression test that expects escaped marker text with assertions
  for genuine CDATA output and XML round-trip behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `moodle-xml-export`: HTML question and answer text is emitted in actual CDATA
  sections, as required by the existing Moodle XML format contract.

## Impact

The change is limited to Moodle XML serialization and its tests. Exported files
will differ at HTML `<text>` nodes, changing from escaped CDATA marker text to
valid CDATA syntax. No database schema, Django model, view, URL, template, or
dependency changes are required.

The primary Python XML risk is accidentally creating malformed output when
content includes the CDATA terminator `]]>`; the existing sanitization remains
in place and receives regression coverage. Verification will run
`poetry run pytest apps/exams/tests.py -k "MarkdownConversion or MoodleXMLGeneration"`
and parse the generated result with the standard-library XML parser.
