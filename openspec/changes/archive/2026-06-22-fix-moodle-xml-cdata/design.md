## Context

`generate_moodle_xml()` builds the document with `xml.etree.ElementTree`, then
passes the serialized result through `xml.dom.minidom` for pretty printing.
ElementTree has no public CDATA node type. Assigning a string that contains
CDATA delimiters to `.text` therefore serializes the delimiters as escaped
character data.

## Goals / Non-Goals

**Goals:**

- Emit genuine CDATA nodes for question and answer HTML.
- Preserve valid Moodle XML structure and readable indentation.
- Keep the existing protection against embedded `]]>` terminators.
- Add regression tests for raw serialization and parsed XML content.

**Non-Goals:**

- Change Markdown rendering or multilingual fallback behavior.
- Change grading, question variants, export views, or download naming.
- Add an XML dependency such as `lxml`.

## Decisions

### 1. Create CDATA nodes in the minidom serialization phase

ElementTree will continue to build the document structure. Question and answer
HTML will initially be assigned as ordinary text without fake CDATA
delimiters. After parsing the ElementTree output into `minidom`, a focused
helper will replace the text children of:

- `questiontext > text`
- `answer > text`

with `Document.createCDATASection()` nodes. `toprettyxml()` will then serialize
those nodes using real CDATA syntax.

This keeps CDATA handling in the XML object model instead of performing string
replacement on serialized XML.

**Alternatives considered:**

- Use serialized string replacement: rejected because matching escaped text is
  brittle and can alter user content or unrelated `<text>` elements.
- Rebuild the complete document with minidom: rejected because it creates a
  larger and riskier rewrite.
- Add `lxml`: rejected because the standard library already supports the
  required DOM CDATA node and no new dependency is justified.

### 2. Keep terminator sanitization before CDATA node creation

`format_html_for_moodle()` will continue replacing `]]>` with `]]&gt;`.
`createCDATASection()` rejects embedded CDATA terminators, so sanitizing before
node creation preserves well-formed output and the current security boundary.

### 3. No Django surface changes

There are no database schema changes, models, fields, or relationships. URL
routing remains the existing exam export endpoint. No templates, template
inheritance, template tags, filters, CSS, JavaScript, or app static files are
added or changed.

## Risks / Trade-offs

- The DOM post-processing helper depends on the current Moodle XML element
  hierarchy. Regression tests will cover both question and answer paths.
- XML parsers expose CDATA content as ordinary text after parsing; tests must
  inspect raw XML to verify CDATA syntax and parsed XML to verify semantic
  content.
- `minidom` remains an in-memory serializer. This change does not alter the
  export's existing memory profile.
