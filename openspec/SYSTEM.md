# Qoodle - System Specification

**Version:** 0.1.0  
**Last Updated:** 2026-02-02  
**Status:** In Development

## Overview

Qoodle is a web application for creating, managing, and exporting Moodle quiz questions with advanced variable substitution and multilingual support. Teachers can create parametric questions with dynamic values, organize them hierarchically by subject, and export multiple variants to Moodle XML format.

## Technology Stack

### Backend
- **Framework:** Django 6.0.1
- **Language:** Python 3.12+
- **Database:** SQLite (development), PostgreSQL (production-ready)
- **Package Management:** Poetry

### Frontend
- **UI Framework:** Bootstrap 5.3.8
- **Icons:** FontAwesome 6.5.1
- **JavaScript:** Vanilla JS (minimal, progressive enhancement)

### Development Tools
- **Testing:** pytest-django
- **Code Quality:** black, ruff, mypy
- **Static Files:** WhiteNoise, django-compressor
- **Coverage:** pytest-cov (target: >80%)

## Architecture

### Project Structure

```
qoodle-ui/
├── apps/                      # All Django applications
│   ├── common/               # Shared utilities and base models
│   │   ├── models.py         # UUIDModel abstract base
│   │   ├── templates/        # Base templates (base.html)
│   │   └── static/           # Common CSS/JS
│   └── subjects/             # Subject hierarchy management
│       ├── models.py         # Subject model
│       ├── views.py          # CRUD views
│       ├── forms.py          # Forms
│       ├── templates/        # Subject templates
│       └── tests.py          # Test suite
├── qoodle/                   # Django project settings
│   ├── settings.py           # Configuration
│   ├── urls.py              # Root URL routing
│   └── wsgi.py              # WSGI entry point
├── openspec/                 # OpenSpec change management
│   └── changes/             # Feature specifications
├── pyproject.toml           # Poetry dependencies
└── pytest.ini               # Test configuration
```

### Design Principles

1. **App-Based Architecture:** Each feature lives in its own Django app under `apps/`
2. **UUID Primary Keys:** All models extend `UUIDModel` for security and consistency
3. **Template Inheritance:** All templates extend `common/base.html`
4. **Static Files per App:** Each app has its own `static/appname/` directory
5. **Type Safety:** Comprehensive type hints throughout
6. **Test-Driven:** >80% coverage requirement, pytest-based testing
7. **Documentation:** Docstrings on all classes and non-trivial methods

## Data Models

### UUIDModel (Abstract Base)

All models in the system extend this abstract base class:

```python
class UUIDModel(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
```

**Purpose:** Ensures consistent UUID usage and automatic timestamp tracking across all models.

### Subject Model

**Location:** `apps.subjects.models.Subject`

Hierarchical subject organization for quiz questions.

**Fields:**
- `id` (UUID) - Primary key
- `name` (CharField) - Subject name
- `parent` (ForeignKey to self, nullable) - Parent subject for hierarchy
- `description` (TextField) - Optional description
- `created_at`, `updated_at` (DateTimeField) - Timestamps

**Key Methods:**
- `get_children()` - Return immediate child subjects
- `get_ancestors()` - Return all parent subjects up to root
- `get_descendants()` - Return all child subjects recursively
- `question_count` - Property returning question count (currently 0)

**Constraints:**
- Unique constraint on (parent, name) - prevents duplicate names at same level
- ON DELETE PROTECT - prevents deletion of subjects with children

## URL Structure

### Root Level
- `/` - Home page
- `/admin/` - Django admin interface

### Subjects
- `/subjects/` - List all subjects (tree view)
- `/subjects/create/` - Create new subject
- `/subjects/create/?parent=<uuid>` - Create sub-subject
- `/subjects/<uuid>/edit/` - Edit subject
- `/subjects/<uuid>/delete/` - Delete subject

## User Interface

### Layout
- **Navigation Bar:** Bootstrap navbar with app branding and main navigation
- **Main Content:** Container-based responsive layout
- **Footer:** Simple copyright footer
- **Messages:** Django messages framework with auto-dismiss (5 seconds)

### Design System
- **Primary Color:** Bootstrap primary blue (#0d6efd)
- **Icons:** FontAwesome 6.5.1
- **Typography:** Bootstrap default (system fonts)
- **Cards:** Used for content grouping
- **Tables:** Responsive tables for list views
- **Forms:** Bootstrap form controls with validation

### Accessibility
- Semantic HTML5 elements
- ARIA labels on interactive elements
- Color contrast compliance
- Keyboard navigation support

## Security

### Implemented
- UUID primary keys (non-sequential, harder to enumerate)
- CSRF protection (Django middleware)
- XSS protection (Django template escaping)
- SQL injection protection (Django ORM)
- Static files fingerprinting (WhiteNoise)

### Authentication (Future)
Currently no authentication - all features are open access. Future iterations will add:
- User registration and login
- Permission-based access control
- Multi-tenancy support

## Testing Strategy

### Test Types
1. **Model Tests:** Business logic, relationships, constraints
2. **View Tests:** HTTP responses, redirects, context data
3. **Form Tests:** Validation, field configuration
4. **Integration Tests:** Full workflows (create → edit → delete)

### Coverage Requirements
- Minimum: 80% overall coverage
- Target: 95%+ for critical paths
- Current: 99% (subjects app)

### Test Execution
```bash
# Run all tests
poetry run pytest

# Run specific app tests
poetry run pytest apps/subjects/tests.py -v

# Generate coverage report
poetry run pytest --cov=apps --cov-report=html
```

## Development Workflow

### Code Standards
- **PEP 8** compliance (enforced by black and ruff)
- **Type hints** on all functions
- **Docstrings** on all classes and non-trivial methods
- **Import ordering:** Standard library → Django → Third party → Local

### Change Management (OpenSpec)
1. Create proposal in `openspec/changes/<id>-<name>/`
2. Document in `PROPOSAL.md`
3. Implement following proposal
4. Test (>80% coverage)
5. Archive in `ARCHIVE.md`

### Git Workflow
- Feature branches from `master`
- Descriptive commit messages
- Commits include related changes (model + views + tests)

## Static Files

### Development
- Static files served directly from app directories
- No collectstatic needed
- STORAGES backend: `StaticFilesStorage`

### Production
- WhiteNoise for static file serving
- STORAGES backend: `CompressedManifestStaticFilesStorage`
- Run `python manage.py collectstatic` before deployment
- django-compressor for CSS/JS minification

## Database

### Development
- SQLite database: `db.sqlite3`
- No additional setup required
- Migrations tracked in version control

### Production Considerations
- PostgreSQL recommended
- UUID native support
- Connection pooling recommended
- Regular backups required

## Performance Considerations

### Query Optimization
- `select_related()` for ForeignKey lookups
- `prefetch_related()` for reverse ForeignKey
- Database indexes on frequently queried fields

### Caching Strategy (Future)
- Django cache framework
- Cache subject tree structure
- Cache question counts
- Redis recommended for production

## Deployment

### Requirements
- Python 3.12+
- PostgreSQL 12+ (production)
- Web server (Gunicorn + Nginx recommended)
- Static file serving (WhiteNoise or CDN)

### Environment Variables
```bash
DEBUG=False
SECRET_KEY=<generate-secure-key>
DATABASE_URL=postgresql://...
ALLOWED_HOSTS=domain.com,www.domain.com
```

### Deployment Checklist
1. Set `DEBUG=False`
2. Configure `ALLOWED_HOSTS`
3. Set strong `SECRET_KEY`
4. Run migrations: `python manage.py migrate`
5. Collect static files: `python manage.py collectstatic`
6. Create superuser: `python manage.py createsuperuser`
7. Configure Gunicorn/uWSGI
8. Set up Nginx reverse proxy
9. Enable HTTPS (Let's Encrypt)
10. Set up monitoring and logging

## Monitoring & Logging

### Logging
- Django logging framework
- Separate logs for errors, warnings, info
- Structured logging recommended for production

### Monitoring (Future)
- Application performance monitoring (APM)
- Error tracking (e.g., Sentry)
- Uptime monitoring
- Database query performance

## Features

### Implemented ✅
- Hierarchical subject management (001-hierarchical-subjects)
- UUID-based models
- Bootstrap UI framework
- Comprehensive testing setup

### In Progress 🚧
- None currently

### Planned 📋
- Question management with variable substitution
- Multilingual question support
- Question variant generation
- Moodle XML export
- User authentication and permissions
- Question bank management

## Configuration

### Django Settings

**Key Settings:**
- `INSTALLED_APPS` - All apps in `apps/` directory
- `MIDDLEWARE` - Includes WhiteNoise for static files
- `STORAGES` - Conditional based on DEBUG flag
- `STATICFILES_FINDERS` - Includes django-compressor

### Poetry Dependencies

**Production:**
- django (^6.0)
- django-compressor (^4.5)
- whitenoise (^6.8)

**Development:**
- pytest (^8.3)
- pytest-django (^4.9)
- pytest-cov (^6.0)
- black (^25.1)
- ruff (^0.9)
- mypy (^1.15)
- django-stubs (^5.2)

## API Design (Future)

When REST API is needed:
- Django REST Framework (DRF)
- Token authentication
- API versioning (v1, v2, etc.)
- OpenAPI/Swagger documentation
- Rate limiting

## Internationalization (Future)

- Django i18n framework
- Translation files in locale/
- Multi-language question support
- Locale-aware formatting

## Browser Support

### Minimum Requirements
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Progressive Enhancement
- Core functionality works without JavaScript
- JavaScript enhances UX (auto-dismiss alerts, etc.)
- Responsive design (mobile-first)

## Known Limitations

1. **No Authentication:** Currently open access to all features
2. **SQLite in Development:** Not suitable for production multi-user scenarios
3. **Simple Hierarchy:** No django-mptt, may have performance issues with deep trees
4. **No Real-time Updates:** Page refresh required to see changes
5. **No Question Counting:** Subject.question_count always returns 0

## Future Architectural Considerations

### Scalability
- Consider Django MPTT for subject hierarchies at scale
- Redis caching for frequently accessed data
- CDN for static files
- Database read replicas

### Extensibility
- Plugin architecture for question types
- Custom export formats beyond Moodle
- Integration with LMS systems
- Question import from various formats

---

**Document Maintained By:** Development Team  
**Review Frequency:** After each major feature  
**Next Review:** After Question Management implementation
