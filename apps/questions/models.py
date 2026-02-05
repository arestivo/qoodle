"""Models for the questions app."""

import random
import re
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
    def generate_string(values: list[str]) -> str:
        """
        Select a random value from the provided list.

        Args:
            values: List of possible string values

        Returns:
            One randomly selected value from the list

        Example:
            generate_string(["apple", "banana", "cherry"]) -> "banana"
        """
        if not values:
            raise ValueError("values list cannot be empty")

        return random.choice(values)

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


class QuestionTemplate(UUIDModel):
    """
    Question template with multilingual and parametric variable support.

    Question templates belong to a subject and contain text that can be provided
    in multiple languages. The first choice (order=0) is always the correct answer.

    ## Variable System

    Questions support parametric variables for generating randomized content.
    Variables are defined in the `variables` JSONField and referenced using
    {{variable}} syntax in question and choice text.

    ### Variable Types

    1. **Numeric (num)**: Random number within range
       ```python
       {
           "x": {
               "type": "num",
               "min": 1,
               "max": 10,
               "precision": 0.5  # Steps: 1.0, 1.5, 2.0, ...
           }
       }
       ```

    2. **String (string)**: Random selection from predefined values
       ```python
       {
           "category": {
               "type": "string",
               "values": ["products", "news", "posts", "articles"]
           }
       }
       ```

    3. **Set (set)**: Random subset from predefined items
       ```python
       {
           "wrong": {
               "type": "set",
               "items": ["A", "B", "C", "D", "E"],
               "size": 3  # Select 3 items
           }
       }
       ```

    4. **Expression (expression)**: Computed from other variables
       ```python
       {
           "a": {"type": "num", "min": 1, "max": 10, "precision": 1},
           "b": {"type": "num", "min": 1, "max": 10, "precision": 1},
           "sum": {
               "type": "expression",
               "formula": "a + b"  # Python expression
           }
       }
       ```

    ### Variable Usage

    Use {{variable}} syntax to reference variables in text:
    ```python
    text = {"en": "What is {{a}} + {{b}}?"}
    choices = [
        {"en": "{{sum}}"},  # Correct answer
        {"en": "{{wrong[0]}}"},  # From set variable
        {"en": "{{wrong[1]}}"},
        {"en": "{{wrong[2]}}"}
    ]
    ```

    ### Rendering Pipeline

    1. **Generate**: `question.generate_variables(seed=42)` creates variable values
    2. **Substitute**: `question.get_text(lang, variables)` replaces {{...}} markers
    3. **Render**: `question.render_text(lang, seed)` applies markdown formatting

    ### Example: Math Problem

    ```python
    question = Question.objects.create(
        subject=math_subject,
        title="Addition Problem",
        text={"en": "Calculate {{x}} + {{y}}"},
        variables={
            "x": {"type": "num", "min": 1, "max": 20, "precision": 1},
            "y": {"type": "num", "min": 1, "max": 20, "precision": 1},
            "answer": {"type": "expression", "formula": "x + y"},
            "wrong": {"type": "set", "items": [str(i) for i in range(50)], "size": 3}
        }
    )
    ```

    ### Validation

    - Variables are evaluated in definition order (expressions can reference earlier variables)
    - Circular dependencies are detected during validation
    - Undefined variable references in text raise ValidationError
    - Invalid variable definitions (missing fields, invalid ranges) are caught
    """

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="question_templates",
        help_text="Subject this question template belongs to",
    )
    title = models.CharField(
        max_length=200,
        default="",
        help_text="Short title to identify this question template",
    )
    text = models.JSONField(
        help_text="Template text in multiple languages (JSON)",
        validators=[validate_multilingual_text],
    )
    variables = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text="Variable definitions for parametric questions (JSON)",
    )
    validation_rules = models.JSONField(
        default=list,
        blank=True,
        help_text="List of validation expressions (e.g., ['a > b', 'a + b > c'])",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Template"
        verbose_name_plural = "Templates"
        indexes = [
            models.Index(fields=["subject", "-created_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the template."""
        return self.title

    def get_absolute_url(self) -> str:
        """Return the URL for this template."""
        return reverse("questions:preview", kwargs={"pk": self.pk})

    def available_languages(self) -> set[str]:
        """Return set of all language codes used in this template."""
        return set(self.text.keys()) if self.text else set()

    def get_all_texts(self) -> dict[str, str]:
        """Return dict of all language versions."""
        return dict(self.text) if self.text else {}

    def generate_variables(self, seed: int = None, max_validation_attempts: int = 100) -> dict[str, Any]:
        """
        Generate values for all variables defined in this template.

        Variables are evaluated in definition order. Expression variables
        can only reference variables defined earlier in the dict.

        If validation_rules are defined, variables are regenerated until
        all rules pass (up to max_validation_attempts).

        Args:
            seed: Optional random seed for reproducibility
            max_validation_attempts: Maximum attempts to generate valid variables (default: 100)

        Returns:
            Dict mapping variable names to generated values

        Raises:
            ValidationError: If invalid definition, missing dependency, or unable to satisfy validation rules

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

        # Generate and validate variables
        for attempt in range(max_validation_attempts):
            generated = self._generate_variables_once()

            if self._validate_rules(generated):
                return generated

        # If we couldn't generate valid variables after max attempts
        raise ValidationError(f"Unable to generate valid variables after {max_validation_attempts} attempts. Validation rules may be too restrictive or incompatible with variable definitions.")

    def _generate_variables_once(self) -> dict[str, Any]:
        """
        Generate values for variables one time without validation.

        Returns:
            Dict mapping variable names to generated values

        Raises:
            ValidationError: If invalid definition or missing dependency
        """
        generated = {}

        # Evaluate variables in order
        for var_name, var_def in self.variables.items():
            var_type = var_def.get("type")

            try:
                if var_type == "num":
                    value = VariableGenerator.generate_num(
                        var_def.get("min", 0),
                        var_def.get("max", 100),
                        var_def.get("precision", 1),
                    )
                elif var_type == "string":
                    value = VariableGenerator.generate_string(
                        var_def.get("values", []),
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

            except (ValueError, ValidationError) as e:
                raise ValidationError(f"Error generating variable '{var_name}': {e}")

        return generated

    def _validate_rules(self, variables: dict[str, Any]) -> bool:
        """
        Check if generated variables pass all validation rules.

        Args:
            variables: Dictionary of generated variable values

        Returns:
            bool: True if all rules pass, False otherwise
        """
        if not self.validation_rules:
            return True

        # Safe built-in functions allowed in rules
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

        # Create evaluation context with generated variables
        context = {**safe_builtins, **variables}

        for rule in self.validation_rules:
            try:
                # Evaluate rule with restricted builtins
                result = eval(rule, {"__builtins__": {}}, context)
                if not result:
                    return False
            except Exception:
                # If rule evaluation fails, treat as validation failure
                return False

        return True

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
            Template text in requested or fallback language with variables substituted

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
            template.render_text(language_code="en", seed=42)
        """
        # Generate variable values
        variables = self.generate_variables(seed=seed)

        # Get text with variable substitution
        text = self.get_text(language_code=language_code, variables=variables)

        # Render markdown if requested
        if markdown:
            text = markdown_lib.markdown(text)

        return text

    def _validate_variable_definition(self) -> None:
        """
        Validate variable definitions structure and required fields.

        Raises:
            ValidationError: If any variable definition is invalid
        """
        if not self.variables:
            return

        for var_name, var_def in self.variables.items():
            # Check var_name is valid Python identifier
            if not var_name.isidentifier():
                raise ValidationError(f"Variable name '{var_name}' is not a valid Python identifier")

            # Check type exists
            if "type" not in var_def:
                raise ValidationError(f"Variable '{var_name}' missing 'type' field")

            var_type = var_def["type"]

            # Validate based on type
            if var_type == "num":
                if "min" not in var_def:
                    raise ValidationError(f"Variable '{var_name}' missing 'min' field")
                if "max" not in var_def:
                    raise ValidationError(f"Variable '{var_name}' missing 'max' field")
                if not isinstance(var_def["min"], (int, float)):
                    raise ValidationError(f"Variable '{var_name}': 'min' must be a number")
                if not isinstance(var_def["max"], (int, float)):
                    raise ValidationError(f"Variable '{var_name}': 'max' must be a number")
                if var_def["min"] > var_def["max"]:
                    raise ValidationError(f"Variable '{var_name}': 'min' cannot be greater than 'max'")
                if "precision" in var_def and not isinstance(var_def["precision"], (int, float)):
                    raise ValidationError(f"Variable '{var_name}': 'precision' must be a number")

            elif var_type == "string":
                if "values" not in var_def:
                    raise ValidationError(f"Variable '{var_name}' missing 'values' field")
                if not isinstance(var_def["values"], list):
                    raise ValidationError(f"Variable '{var_name}': 'values' must be a list")
                if not var_def["values"]:
                    raise ValidationError(f"Variable '{var_name}': 'values' cannot be empty")

            elif var_type == "set":
                if "items" not in var_def:
                    raise ValidationError(f"Variable '{var_name}' missing 'items' field")
                if "size" not in var_def:
                    raise ValidationError(f"Variable '{var_name}' missing 'size' field")
                if not isinstance(var_def["items"], list):
                    raise ValidationError(f"Variable '{var_name}': 'items' must be a list")
                if not isinstance(var_def["size"], int):
                    raise ValidationError(f"Variable '{var_name}': 'size' must be an integer")
                if var_def["size"] < 0:
                    raise ValidationError(f"Variable '{var_name}': 'size' cannot be negative")
                if var_def["size"] > len(var_def["items"]):
                    raise ValidationError(f"Variable '{var_name}': 'size' ({var_def['size']}) cannot exceed items count ({len(var_def['items'])})")

            elif var_type == "expression":
                if "formula" not in var_def:
                    raise ValidationError(f"Variable '{var_name}' missing 'formula' field")
                if not isinstance(var_def["formula"], str):
                    raise ValidationError(f"Variable '{var_name}': 'formula' must be a string")
                if not var_def["formula"].strip():
                    raise ValidationError(f"Variable '{var_name}': 'formula' cannot be empty")

            else:
                raise ValidationError(f"Variable '{var_name}': unknown type '{var_type}'")

    def _validate_text_references(self) -> None:
        """
        Validate that all {{variable}} references in text exist in variables definition.

        Checks both template text (all languages) and all choice texts.

        Raises:
            ValidationError: If undefined variables are referenced
        """
        if not self.text:
            return

        # Collect all {{...}} references from template text
        all_references = set()
        pattern = r"\{\{([^}]+)\}\}"

        # Check template text in all languages
        for lang_text in self.text.values():
            matches = re.findall(pattern, lang_text)
            for match in matches:
                # Extract variable names from the match
                var_names = re.findall(r"\b([a-zA-Z_]\w*)\b", match)
                all_references.update(var_names)

        # Check choice texts (if template has been saved and has choices)
        if self.pk:
            for choice in self.choices.all():
                for lang_text in choice.text.values():
                    matches = re.findall(pattern, lang_text)
                    for match in matches:
                        var_names = re.findall(r"\b([a-zA-Z_]\w*)\b", match)
                        all_references.update(var_names)

        # Filter out safe builtins that are allowed in expressions
        safe_builtins = {
            "abs",
            "round",
            "min",
            "max",
            "int",
            "float",
            "str",
            "len",
            "sum",
        }
        all_references -= safe_builtins

        # Check if all referenced variables are defined
        if all_references:
            defined_vars = set(self.variables.keys()) if self.variables else set()
            undefined = all_references - defined_vars

            if undefined:
                raise ValidationError(f"Undefined variables referenced in text: {sorted(undefined)}")

    def clean(self) -> None:
        """
        Validate the template including variable definitions.

        Called by Django's model validation before save.

        Raises:
            ValidationError: If any validation fails
        """
        super().clean()

        # Skip validation if no variables defined
        if not self.variables:
            return

        # Run all validation methods
        try:
            self._validate_variable_definition()
            self._validate_text_references()

            # Try test-evaluation with seed=0 to catch any runtime errors
            test_vars = self.generate_variables(seed=0)

            # Try substitution on all text variants
            for lang_text in self.text.values():
                self._substitute_variables(lang_text, test_vars)

        except ValidationError:
            # Re-raise ValidationErrors as-is
            raise
        except Exception as e:
            # Wrap other exceptions in ValidationError
            raise ValidationError(f"Variable validation error: {e}")

    @property
    def choice_count(self) -> int:
        """Return the number of choices for this template."""
        return self.choices.count()

    @property
    def correct_choice(self):
        """Return the correct choice (first choice with order=0)."""
        return self.choices.filter(order=0).first()


class Choice(UUIDModel):
    """
    Multiple choice option with multilingual support.

    Important: The first choice (order=0) is always the correct answer.
    When displaying templates to students, choices should be randomized.
    """

    template = models.ForeignKey(
        QuestionTemplate,
        on_delete=models.CASCADE,
        related_name="choices",
        help_text="Question template this choice belongs to",
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

        # Substitute variables if provided (reuse QuestionTemplate's method)
        if variables and self.template:
            text = self.template._substitute_variables(text, variables)

        return text

    def render_text(self, language_code: str = None, variables: dict[str, Any] = None, markdown: bool = True) -> str:
        """
        Convenience method: render text with variables and markdown.

        Args:
            language_code: Optional language code
            variables: Optional dict of variable values (usually from template.generate_variables())
            markdown: Whether to render as markdown (default: True)

        Returns:
            Rendered text with variables substituted and markdown applied

        Example:
            # Generate variables from template
            variables = choice.template.generate_variables(seed=42)
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
