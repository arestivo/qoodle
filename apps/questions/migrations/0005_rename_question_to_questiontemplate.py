"""Migration to rename Question model to QuestionTemplate."""

from django.db import migrations


class Migration(migrations.Migration):
    """Rename Question to QuestionTemplate to reflect template-based nature."""

    dependencies = [
        ("questions", "0004_question_validation_rules"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Question",
            new_name="QuestionTemplate",
        ),
    ]
