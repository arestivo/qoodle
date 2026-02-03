"""Models for the questions app."""

import random
import re
import string
from typing import Any

import markdown as markdown_lib
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from apps.common.models import UUIDModel
from apps.subjects.models import Subject


def validate_multilingual_text(value):
    """
    Validate multilingual text JSON structure.

    Requirements:
    - Must be a dict
    - Must have at least one language key
    - All values must be non-empty strings
    - Keys should be valid language codes or "none"
    """
    if not isinstance(value, dict):
        raise ValidationError("Multilingual text must be a dictionary")

    if not value:
        raise ValidationError("Must provide text in at least one language")

    for key, text in value.items():
        if not isinstance(text, str) or not text.strip():
            raise ValidationError(f"Text for language '{key}' must be a non-empty string")


class VariableGenerator:
    """
    Helper class for generating random variable values.

    Supports four variable types:
    - num: Random number within range with specified precision
    - string: Random string within length range
    - set: Random subset of specified size from item list
    - expression: Evaluated Python expression using other variables
    """

    @staticmethod
    def generate_num(min_val: float, max_val: float, precision: float = 1) -> float:
        """
        Generate random number between min and max with given precision.

        Args:
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)
            precision: Step size (default: 1 for integers)

        Returns:
            Random number as float

        Example:
            generate_num(1, 10, 0.5) -> 1.0, 1.5, 2.0, ..., 10.0
        """
        if min_val > max_val:
            raise ValueError(f"min_val ({min_val}) cannot be greater than max_val ({max_val})")

        # Calculate number of steps
        steps = int((max_val - min_val) / precision)
        if steps == 0:
            return min_val

        # Generate random step and calculate value
        random_step = random.randint(0, steps)
        value = min_val + (random_step * precision)

        # Round to precision to avoid floating point errors
        decimal_places = len(str(precision).split(".")[-1]) if "." in str(precision) else 0
        return round(value, decimal_places)

    @staticmethod
    def generate_string(min_length: int, max_length: int) -> str:
        """
        Generate random string with length between min and max.

        Args:
            min_length: Minimum string length
            max_length: Maximum string length

        Returns:
            Random lowercase string

        Example:
            generate_string(3, 5) -> "abc", "wxyz", "hello"
        """
        if min_length > max_length:
            raise ValueError(f"min_length ({min_length}) cannot be greater than max_length ({max_length})")

        if min_length < 0:
            raise ValueError("min_length cannot be negative")

        length = random.randint(min_length, max_length)
        return "".join(random.choices(string.ascii_lowercase, k=length))

    @staticmethod
    def generate_set(items: list[str], size: int) -> list[str]:
        """
        Generate random subset of specified size from items.

        Args:
            items: List of items to choose from
            size: Number of items to select

        Returns:
            Random subset as list

        Raises:
            ValueError: If size > len(items)

        Example:
            generate_set(["red", "blue", "green"], 2) -> ["red", "green"]
        """
        if size > len(items):
            raise ValueError(f"Cannot select {size} items from {len(items)} available items")

        if size < 0:
            raise ValueError("size cannot be negative")

        return random.sample(items, size)

    @staticmethod
    def evaluate_expression(formula: str, context: dict[str, Any]) -> Any:
        """
        Evaluate Python expression with variables from context.

        Args:
            formula: Python expression string
            context: Dict of variable names to values

        Returns:
            Evaluated result

        Raises:
            ValidationError: If expression evaluation fails

        Example:
            evaluate_expression("a + b * 2", {"a": 5, "b": 3}) -> 11
        """
        try:
            # Safe built-in functions allowed in expressions
            safe_builtins = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "int": int,
                "float": float,
                "str": str,
                "len": len,
                "sum": sum,
            }
            # Merge safe builtins with variable context
            namespace = {**safe_builtins, **context}

            # Evaluate with restricted builtins
            return eval(formula, {"__builtins__": {}}, namespace)
        except Exception as e:
            raise ValidationError(f"Expression evaluation failed: {e}")


class Question(UUIDModel):
    """
    Quiz question with multilingual support.

    Questions belong to a subject and contain text that can be provided
    in multiple languages. The first choice (order=0) is always the correct answer.
    """

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="questions",
        help_text="Subject this question belongs to",
    )
    title = models.CharField(
        max_length=200,
        default="no title",
        help_text="Short title to identify this question",
    )
    text = models.JSONField(
        help_text="Question text in multiple languages (JSON)",
        validators=[validate_multilingual_text],
    )
    variables = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text="Variable definitions for parametric questions (JSON)",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        indexes = [
            models.Index(fields=["subject", "-created_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the question."""
        return self.title

    def get_absolute_url(self) -> str:
        """Return the URL for this question."""
        return reverse("questions:preview", kwargs={"pk": self.pk})

    def available_languages(self) -> set[str]:
        """Return set of all language codes used in this question."""
        return set(self.text.keys()) if self.text else set()

    def get_all_texts(self) -> dict[str, str]:
        """Return dict of all language versions."""
        return dict(self.text) if self.text else {}

    def generate_variables(self, seed: int = None) -> dict[str, Any]:
        """
        Generate values for all variables defined in this question.

        Handles dependencies between variables using topological sort.
        Variables of type 'expression' can reference other variables.

        Args:
            seed: Optional random seed for reproducibility

        Returns:
            Dict mapping variable names to generated values

        Raises:
            ValidationError: If circular dependency or invalid definition detected

        Example:
            variables = {"a": {"type": "num", "min": 1, "max": 10, "precision": 1},
                        "b": {"type": "expression", "formula": "a * 2"}}
            generate_variables() -> {"a": 7, "b": 14}
        """
        if not self.variables:
            return {}

        # Set random seed if provided
        if seed is not None:
            random.seed(seed)

        # Topological sort to handle dependencies
        generated = {}
        remaining = dict(self.variables)
        max_iterations = len(remaining) + 1
        iteration = 0

        while remaining and iteration < max_iterations:
            iteration += 1
            made_progress = False

            for var_name in list(remaining.keys()):
                var_def = remaining[var_name]
                var_type = var_def.get("type")

                # Check if dependencies are satisfied
                if var_type == "expression":
                    # Extract variable names from formula
                    formula = var_def.get("formula", "")
                    dependencies = set(re.findall(r"\b([a-zA-Z_]\w*)\b", formula))
                    # Filter to only include our defined variables
                    dependencies = {d for d in dependencies if d in self.variables}

                    # Skip if dependencies not yet generated
                    if not all(d in generated for d in dependencies):
                        continue

                # Generate value based on type
                try:
                    if var_type == "num":
                        value = VariableGenerator.generate_num(
                            var_def.get("min", 0),
                            var_def.get("max", 100),
                            var_def.get("precision", 1),
                        )
                    elif var_type == "string":
                        value = VariableGenerator.generate_string(
                            var_def.get("min_length", 1),
                            var_def.get("max_length", 10),
                        )
                    elif var_type == "set":
                        value = VariableGenerator.generate_set(
                            var_def.get("items", []),
                            var_def.get("size", 1),
                        )
                    elif var_type == "expression":
                        value = VariableGenerator.evaluate_expression(
                            var_def.get("formula", ""),
                            generated,
                        )
                    else:
                        raise ValidationError(f"Unknown variable type: {var_type}")

                    generated[var_name] = value
                    del remaining[var_name]
                    made_progress = True

                except (ValueError, ValidationError) as e:
                    raise ValidationError(f"Error generating variable '{var_name}': {e}")

            # If no progress made, we have a circular dependency
            if not made_progress and remaining:
                raise ValidationError(f"Circular dependency detected in variables: {list(remaining.keys())}")

        return generated

    def _substitute_variables(self, text: str, variables: dict[str, Any]) -> str:
        """
        Replace {{variable}} and {{expression}} placeholders in text.

        Args:
            text: Text containing variable placeholders
            variables: Dict of variable names to values

        Returns:
            Text with all placeholders replaced

        Example:
            _substitute_variables("The value is {{a}}", {"a": 5}) -> "The value is 5"
            _substitute_variables("Sum is {{a + b}}", {"a": 2, "b": 3}) -> "Sum is 5"
        """
        if not text or not variables:
            return text

        def replace_placeholder(match):
            """Replace single placeholder with evaluated value."""
            placeholder = match.group(1).strip()

            # Try direct variable lookup first
            if placeholder in variables:
                value = variables[placeholder]
                # Format lists nicely
                if isinstance(value, list):
                    return ", ".join(str(v) for v in value)
                return str(value)

            # Try evaluating as expression
            try:
                result = VariableGenerator.evaluate_expression(placeholder, variables)
                if isinstance(result, list):
                    return ", ".join(str(v) for v in result)
                return str(result)
            except ValidationError:
                # If evaluation fails, leave placeholder as-is
                return match.group(0)

        # Find and replace all {{...}} patterns
        pattern = r"\{\{([^}]+)\}\}"
        return re.sub(pattern, replace_placeholder, text)

    def get_text(self, language_code: str = None, variables: dict[str, Any] = None) -> str:
        """
        Get text for specific language with variable substitution.

        Fallback order:
        1. Requested language (if specified and exists)
        2. Language-independent version ("none" key)
        3. First available language (alphabetically)

        Args:
            language_code: Optional language code to retrieve
            variables: Optional dict of variable values for substitution

        Returns:
            Question text in requested or fallback language with variables substituted

        Raises:
            ValueError: If no text available in any language
        """
        if not self.text:
            raise ValueError("No text available")

        # Try requested language
        if language_code and language_code in self.text:
            text = self.text[language_code]
        # Try language-independent
        elif "none" in self.text:
            text = self.text["none"]
        # Fallback to any available language
        else:
            available = sorted(self.text.keys())
            if available:
                text = self.text[available[0]]
            else:
                raise ValueError("No text available in any language")

        # Substitute variables if provided
        if variables:
            text = self._substitute_variables(text, variables)

        return text

    def render_text(self, language_code: str = None, seed: int = None, markdown: bool = True) -> str:
        """
        Convenience method: generate variables and render text with markdown.

        Args:
            language_code: Optional language code
            seed: Optional random seed for variable generation
            markdown: Whether to render as markdown (default: True)

        Returns:
            Rendered text with variables substituted and markdown applied

        Example:
            question.render_text(language_code="en", seed=42)
        """
        # Generate variable values
        variables = self.generate_variables(seed=seed)

        # Get text with variable substitution
        text = self.get_text(language_code=language_code, variables=variables)

        # Render markdown if requested
        if markdown:
            text = markdown_lib.markdown(text)

        return text

    @property
    def choice_count(self) -> int:
        """Return the number of choices for this question."""
        return self.choices.count()

    @property
    def correct_choice(self):
        """Return the correct choice (first choice with order=0)."""
        return self.choices.filter(order=0).first()


class Choice(UUIDModel):
    """
    Multiple choice option with multilingual support.

    Important: The first choice (order=0) is always the correct answer.
    When displaying questions to students, choices should be randomized.
    """

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
        help_text="Question this choice belongs to",
    )
    text = models.JSONField(
        help_text="Choice text in multiple languages (JSON)",
        validators=[validate_multilingual_text],
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Order of choice (0 = correct answer)",
    )

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = "Choice"
        verbose_name_plural = "Choices"

    def __str__(self) -> str:
        """Return string representation of the choice."""
        try:
            text = self.get_text()[:50]
            return f"{text} {'✓' if self.is_correct else ''}"
        except (ValueError, KeyError):
            return f"Choice {self.id}"

    def get_text(self, language_code: str = None, variables: dict[str, Any] = None) -> str:
        """
        Get text for specific language with variable substitution.

        Fallback order:
        1. Requested language (if specified and exists)
        2. Language-independent version ("none" key)
        3. First available language (alphabetically)

        Args:
            language_code: Optional language code to retrieve
            variables: Optional dict of variable values for substitution

        Returns:
            Choice text in requested or fallback language with variables substituted

        Raises:
            ValueError: If no text available in any language
        """
        if not self.text:
            raise ValueError("No text available")

        # Try requested language
        if language_code and language_code in self.text:
            text = self.text[language_code]
        # Try language-independent
        elif "none" in self.text:
            text = self.text["none"]
        # Fallback to any available language
        else:
            available = sorted(self.text.keys())
            if available:
                text = self.text[available[0]]
            else:
                raise ValueError("No text available in any language")

        # Substitute variables if provided (reuse Question's method)
        if variables and self.question:
            text = self.question._substitute_variables(text, variables)

        return text

    def render_text(self, language_code: str = None, variables: dict[str, Any] = None, markdown: bool = True) -> str:
        """
        Convenience method: render text with variables and markdown.

        Args:
            language_code: Optional language code
            variables: Optional dict of variable values (usually from question.generate_variables())
            markdown: Whether to render as markdown (default: True)

        Returns:
            Rendered text with variables substituted and markdown applied

        Example:
            # Generate variables from question
            variables = choice.question.generate_variables(seed=42)
            # Render choice with those variables
            choice.render_text(language_code="en", variables=variables)
        """
        # Get text with variable substitution
        text = self.get_text(language_code=language_code, variables=variables)

        # Render markdown if requested
        if markdown:
            text = markdown_lib.markdown(text)

        return text

    @property
    def is_correct(self) -> bool:
        """Return True if this is the correct answer (order=0)."""
        return self.order == 0
