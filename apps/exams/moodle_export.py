"""Moodle XML export functionality for exams.

This module provides functions to export exams to Moodle XML format with:
- Variable substitution for question variants
- Language-specific content extraction
- Grading mode-based fraction calculation
- Markdown to HTML conversion with CDATA wrapping
"""

import hashlib
import xml.etree.ElementTree as ET
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from xml.dom import minidom

import markdown

if TYPE_CHECKING:
    from apps.exams.models import Exam
    from apps.questions.models import QuestionTemplate


def calculate_fractions(num_choices: int, grading_mode: str) -> dict[str, Decimal]:
    """Calculate answer fractions for Moodle XML export.

    Args:
        num_choices: Number of answer choices in the question
        grading_mode: Either 'single' or 'multi'

    Returns:
        Dictionary with 'correct' and 'wrong' fraction percentages

    Raises:
        ValueError: If num_choices < 2 or if multi mode with >6 choices

    Examples:
        >>> calculate_fractions(4, 'single')
        {'correct': Decimal('100.0'), 'wrong': Decimal('-33.33333')}

        >>> calculate_fractions(4, 'multi')
        {'correct': Decimal('70.0'), 'wrong': Decimal('10.0')}
    """
    if num_choices < 2:
        raise ValueError(f"Questions must have at least 2 choices, got {num_choices}")

    if grading_mode == "single":
        # Formula: wrong penalty = -100 / (num_choices - 1)
        # Examples: 2 choices=-100%, 3=-50%, 4=-33.33%, 5=-25%, 6=-20%
        wrong_fraction = -100.0 / (num_choices - 1)
        return {"correct": Decimal("100.0"), "wrong": Decimal(str(round(wrong_fraction, 2)))}

    # Multi-choice schemes (hardcoded for pattern tracking)
    schemes = {
        2: {"correct": Decimal("90.0"), "wrong": Decimal("10.0")},
        3: {"correct": Decimal("80.0"), "wrong": Decimal("10.0")},
        4: {"correct": Decimal("70.0"), "wrong": Decimal("10.0")},
        5: {"correct": Decimal("60.0"), "wrong": Decimal("10.0")},
        6: {"correct": Decimal("75.0"), "wrong": Decimal("5.0")},
    }

    if num_choices not in schemes:
        raise ValueError(f"Multi-choice grading only supports 2-6 choices, got {num_choices}")

    return schemes[num_choices]


def format_html_for_moodle(markdown_text: str) -> str:
    """Convert markdown to HTML suitable for Moodle CDATA sections.

    Args:
        markdown_text: Markdown formatted text

    Returns:
        HTML string ready for CDATA wrapping

    Note:
        Escapes ]]> to prevent CDATA injection attacks
    """
    md = markdown.Markdown(
        extensions=[
            "nl2br",  # Newlines → <br>
            "fenced_code",  # ``` code blocks
            "tables",
            "sane_lists",
        ]
    )

    html = md.convert(markdown_text)

    # Prevent CDATA injection
    if "]]>" in html:
        html = html.replace("]]>", "]]&gt;")

    return html


def generate_variant(template: "QuestionTemplate", version_number: int, language: str) -> dict[str, Any]:
    """Generate deterministic question variant using template's built-in methods.

    Args:
        template: QuestionTemplate instance with text and variables
        version_number: Version number (0-based) for seed generation
        language: Target language code

    Returns:
        Dictionary with 'text' and 'values' keys

    Note:
        Uses MD5 hash of template.id + version for deterministic seeding.
        Delegates to QuestionTemplate.generate_variables() and get_text().
    """
    # Create deterministic seed from template ID and version
    seed_string = f"{template.id}_{version_number}"
    seed = int(hashlib.md5(seed_string.encode()).hexdigest(), 16) % (2**32)

    # Use template's generate_variables method with deterministic seed
    values = template.generate_variables(seed=seed) if template.variables else {}

    # Strict validation: Check if the exact language or "none" exists (no fallback to other languages)
    available_langs = template.text.keys() if template.text else []
    if language not in available_langs and "none" not in available_langs:
        raise ValueError(f"Question '{template.title}' does not have text in language '{language}' or a language-independent version. Available: {', '.join(sorted(available_langs)) if available_langs else 'none'}")

    # Use template's get_text method for language extraction and variable substitution
    text = template.get_text(language_code=language, variables=values)

    return {"text": text, "values": values}


def get_choices_for_variant(template: "QuestionTemplate", variant: dict, language: str) -> list[dict]:
    """Get answer choices with variable substitution using Choice.get_text().

    Args:
        template: QuestionTemplate instance
        variant: Variant dictionary from generate_variant()
        language: Target language code

    Returns:
        List of choice dictionaries with 'text' and 'is_correct' keys

    Note:
        First choice (order=0) is always marked as correct.
        Uses Choice.get_text() for language extraction and variable substitution.
    """
    choices = []

    for choice in template.choices.all().order_by("order"):
        # Strict validation: Check if the exact language or "none" exists (no fallback to other languages)
        available_langs = choice.text.keys() if choice.text else []
        if language not in available_langs and "none" not in available_langs:
            raise ValueError(f"Choice {choice.order + 1} in question '{template.title}' does not have text in language '{language}' or a language-independent version. Available: {', '.join(sorted(available_langs)) if available_langs else 'none'}")

        # Use Choice's get_text method for language extraction and variable substitution
        choice_text = choice.get_text(language_code=language, variables=variant["values"])

        choices.append(
            {
                "text": choice_text,
                "is_correct": choice.order == 0,  # First choice is correct
            }
        )

    return choices


def generate_all_variants(template: "QuestionTemplate", num_versions: int, language: str) -> list[dict]:
    """Generate unique question variants with collision detection.

    Args:
        template: QuestionTemplate instance
        num_versions: Number of variants to generate
        language: Target language code

    Returns:
        List of variant dictionaries

    Raises:
        ValueError: If unable to generate unique variants after 50 attempts

    Note:
        Uniqueness is determined by comparing question text + choices as a set.
        This ensures that questions with the same text but different choices
        (e.g., using variables only in choices) are considered unique.
    """
    max_attempts = 50

    for attempt in range(max_attempts):
        variants = []

        for version in range(num_versions):
            # For retry attempts, modify the seed string
            if attempt > 0:
                import copy

                temp_template = copy.copy(template)
                temp_template.id = f"{template.id}_attempt{attempt}"
                variant = generate_variant(temp_template, version, language)
            else:
                variant = generate_variant(template, version, language)

            # Get choices for this variant
            choices = get_choices_for_variant(template, variant, language)
            variant["choices"] = choices

            variants.append(variant)

        # Check uniqueness by comparing question text + choices (as a set since order doesn't matter)
        variant_signatures = []
        for v in variants:
            # Create a unique signature: question text + sorted choice texts
            choice_texts = sorted([c["text"] for c in v["choices"]])
            signature = (v["text"], tuple(choice_texts))
            variant_signatures.append(signature)

        unique_signatures = set(variant_signatures)

        if len(variant_signatures) == len(unique_signatures):  # All unique
            return variants

    # Failed after max attempts
    raise ValueError(f"Could not generate {num_versions} unique variants for template '{template.title}' (ID: {template.id}) after {max_attempts} attempts. Consider widening variable ranges or reducing number of versions.")


def generate_moodle_xml(exam: "Exam", language: str) -> str:
    """Generate Moodle XML for exam export.

    Args:
        exam: Exam instance with pools and templates
        language: Target language code for export

    Returns:
        Pretty-printed XML string in Moodle format

    Raises:
        ValueError: If exam has validation issues
    """

    # Validate exam has pools
    if not exam.pools.exists():
        raise ValueError("Cannot export exam with no question pools")

    quiz = ET.Element("quiz")

    question_number = 1

    for pool in exam.pools.all().order_by("order"):
        # Validate pool has templates
        pool_templates = pool.pool_templates.all()
        if not pool_templates.exists():
            raise ValueError(f"Pool {pool.order} has no templates")

        for pool_template in pool_templates:
            template = pool_template.template

            # Validate template has choices
            if not template.choices.exists():
                raise ValueError(f"Template '{template.title}' has no answer choices")

            num_versions = pool_template.number_of_versions

            # Generate variants
            variants = generate_all_variants(template, num_versions, language)

            for variant in variants:
                question = ET.SubElement(quiz, "question", type="multichoice")

                # Name
                name = ET.SubElement(question, "name")
                name_text = ET.SubElement(name, "text")
                name_text.text = f"Q{question_number}"

                # Tags
                tags = ET.SubElement(question, "tags")
                tag = ET.SubElement(tags, "tag")
                tag_text = ET.SubElement(tag, "text")
                tag_text.text = f"q{question_number}"

                # Question text (CDATA-wrapped HTML)
                html = format_html_for_moodle(variant["text"])
                questiontext = ET.SubElement(question, "questiontext", format="html")
                text_elem = ET.SubElement(questiontext, "text")
                text_elem.text = f"<![CDATA[{html}]]>"

                # Answers with fractions
                # Choices are already in the variant dict from generate_all_variants
                choices = variant["choices"]
                fractions = calculate_fractions(len(choices), exam.grading_mode)

                for choice in choices:
                    fraction = fractions["correct"] if choice["is_correct"] else fractions["wrong"]
                    answer = ET.SubElement(question, "answer", fraction=str(fraction))

                    html_choice = format_html_for_moodle(choice["text"])
                    choice_text = ET.SubElement(answer, "text")
                    choice_text.text = f"<![CDATA[{html_choice}]]>"

                # Single attribute (true for single-choice, false for multi-choice)
                single_value = "true" if exam.grading_mode == "single" else "false"
                single = ET.SubElement(question, "single")
                single.text = single_value

                # Shuffle answers
                shuffle = ET.SubElement(question, "shuffleanswers")
                shuffle.text = "1"

                # Answer numbering
                numbering = ET.SubElement(question, "answernumbering")
                numbering.text = "abc"

                # Default grade
                defaultgrade = ET.SubElement(question, "defaultgrade")
                defaultgrade.text = str(pool.default_grade)

                question_number += 1

    # Pretty-print XML
    xml_string = ET.tostring(quiz, encoding="unicode")
    dom = minidom.parseString(xml_string)
    return dom.toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
