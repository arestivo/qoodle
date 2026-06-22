## MODIFIED Requirements

### Requirement: Moodle XML Generation

The system MUST generate valid Moodle 4.x XML in which rendered HTML for each
question and answer is stored in a genuine CDATA section. The serializer must
not encode the CDATA delimiters as ordinary text.

#### Scenario: Export question HTML as CDATA

- **GIVEN** an exportable exam containing a question whose Markdown renders to
  `<p>In an HTML document...</p>`
- **WHEN** the Moodle XML export is generated
- **THEN** the question text contains
  `<text><![CDATA[<p>In an HTML document...</p>]]></text>`
- **AND** the question text does not contain `&lt;![CDATA[`
- **AND** the complete export can be parsed as XML

#### Scenario: Export answer HTML as CDATA

- **GIVEN** an exportable exam containing answer choices rendered as HTML
- **WHEN** the Moodle XML export is generated
- **THEN** every answer `<text>` element contains a genuine CDATA section
- **AND** parsing the XML returns the rendered HTML as the element text

#### Scenario: Protect the CDATA terminator

- **GIVEN** question or answer content containing `]]>`
- **WHEN** the Moodle XML export is generated
- **THEN** the content cannot terminate the surrounding CDATA section early
- **AND** the complete export remains well-formed XML
