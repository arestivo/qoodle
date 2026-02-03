"""Migration to rename Choice.question FK to Choice.template."""

from django.db import migrations


class Migration(migrations.Migration):
    """Rename Choice.question field to template for consistency."""

    dependencies = [
        ("questions", "0005_rename_question_to_questiontemplate"),
    ]

    operations = [
        migrations.RenameField(
            model_name="choice",
            old_name="question",
            new_name="template",
        ),
    ]
