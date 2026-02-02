# Qoodle - Moodle Quiz Question Generator

A Django-based web application for creating, managing, and exporting Moodle quiz questions with advanced variable substitution and multilingual support.

## Features

- **Parametric Questions**: Create quiz questions with dynamic variable substitution
- **Multiple Variants**: Generate multiple question variants automatically
- **Hierarchical Organization**: Organize questions by subject and topic
- **Multilingual Support**: Create questions in multiple languages
- **Moodle XML Export**: Export questions to Moodle XML format

## Technology Stack

- **Python**: 3.12+
- **Django**: 6.0+
- **Frontend**: Bootstrap 5.3.8, FontAwesome 7.1.0
- **Package Management**: Poetry
- **Testing**: pytest-django

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Poetry package manager

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd qoodle-ui
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Run database migrations:
   ```bash
   poetry run python manage.py migrate
   ```

4. Create a superuser (optional):
   ```bash
   poetry run python manage.py createsuperuser
   ```

5. Run the development server:
   ```bash
   poetry run python manage.py runserver
   ```

6. Open your browser to `http://127.0.0.1:8000/`

## Project Structure

```
qoodle-ui/
├── apps/                   # Django applications
│   ├── common/            # Common/shared functionality
│   │   ├── static/        # Static files (CSS, JS)
│   │   ├── templates/     # HTML templates
│   │   └── templatetags/  # Custom template tags
│   └── ...                # Other apps will be added here
├── qoodle/                # Main Django project settings
├── pyproject.toml         # Poetry dependencies
└── manage.py              # Django management script
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black .
```

### Linting

```bash
poetry run ruff check .
```

### Type Checking

```bash
poetry run mypy .
```

### Collecting Static Files

For production deployment:

```bash
poetry run python manage.py collectstatic
```

## Django Apps Structure

All Django apps are located in the `apps/` directory. Each app follows this structure:

- `templates/appname/` - App-specific templates
- `static/appname/` - App-specific static files
- `models.py` - Database models
- `views.py` - View logic
- `urls.py` - URL routing
- `forms.py` - Form definitions
- `tests/` - Test files

## Contributing

1. Follow PEP 8 coding standards
2. Add type hints to all functions
3. Write comprehensive docstrings
4. Maintain >80% test coverage
5. Use `poetry` for all dependency management
6. Prefix all Python commands with `poetry run`

## License

[Add your license information here]

## Contact

[Add your contact information here]
