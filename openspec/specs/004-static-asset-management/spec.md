# Specification: Static Asset Management

**ID:** 004-static-asset-management  
**Status:** Implemented  
**Version:** 1.0  
**Last Updated:** 2026-02-03  
**Change:** N/A (foundational infrastructure)

## Overview

Per-app static file organization with django-compressor for CSS/JavaScript bundling, minification, and cache-busting. Each Django app contains its own `static/appname/` folder. No global `static/` directory exists. Bootstrap 5.3.8 and FontAwesome 7.1.0 provide UI components.

## Purpose

- Organize static files by Django app for modularity
- Compress and minify CSS/JavaScript for production
- Enable cache-busting with hashed filenames
- Use `defer` attribute to eliminate `DOMContentLoaded` wrappers
- Provide consistent frontend framework (Bootstrap 5.3)
- Support FontAwesome icons throughout the application

## Architecture

### Directory Structure

```
qoodle-ui/
├── apps/
│   ├── common/
│   │   └── static/
│   │       └── common/
│   │           ├── css/
│   │           │   └── main.css          # Global styles
│   │           └── js/
│   │               └── main.js            # Alert auto-dismiss
│   ├── questions/
│   │   └── static/
│   │       └── questions/
│   │           └── js/
│   │               ├── question_form.js   # Choice management
│   │               └── question_list.js   # Auto-filter
│   └── subjects/
│       └── static/
│           └── subjects/
│               └── js/
│                   └── subject_tree.js    # Recursive tree UI
└── staticfiles/                            # Collected files (gitignored)
```

**Key Rules:**
- Each app has `static/appname/` subdirectory
- No global `static/` folder at project root
- Files namespaced by app name to avoid conflicts
- Collected files go to `staticfiles/` (for deployment)

## Django Settings

### Static Files Configuration

```python
# settings.py

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',  # For django-compressor
]

# Installed Apps
INSTALLED_APPS = [
    # ...
    'compressor',
    # ...
]

# Django Compressor Settings
COMPRESS_ENABLED = not DEBUG  # Only compress in production
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.rCSSMinFilter',
]
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
]
COMPRESS_STORAGE = 'compressor.storage.GzipCompressorFileStorage'
COMPRESS_OFFLINE = True  # Generate compressed files during collectstatic
```

## Base Template Structure

### Location
`apps/common/templates/common/base.html`

### HTML Structure

```django
{% load static %}
{% load compress %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Qoodle{% endblock %}</title>
    
    {# Bootstrap CSS #}
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" 
          rel="stylesheet" 
          integrity="sha384-..." 
          crossorigin="anonymous">
    
    {# FontAwesome #}
    <link rel="stylesheet" 
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.1.0/css/all.min.css" 
          integrity="sha384-..." 
          crossorigin="anonymous">
    
    {# Compressed App CSS #}
    {% compress css %}
        <link rel="stylesheet" href="{% static 'common/css/main.css' %}">
        {% block extra_css %}{% endblock %}
    {% endcompress %}
</head>
<body>
    {% include 'common/_navbar.html' %}
    
    <main class="container my-4">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show" 
                     role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endif %}
        
        {% block content %}{% endblock %}
    </main>
    
    {# Bootstrap JS Bundle #}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js" 
            integrity="sha384-..." 
            crossorigin="anonymous"
            defer></script>
    
    {# Compressed App JavaScript #}
    {% compress js %}
        <script src="{% static 'common/js/main.js' %}" defer></script>
        {% block extra_js %}{% endblock %}
    {% endcompress %}
</body>
</html>
```

## Defer Loading Pattern

### JavaScript Loading Strategy

**All JavaScript uses `defer` attribute:**
```html
<script src="script.js" defer></script>
```

**Benefits:**
- Scripts load asynchronously without blocking HTML parsing
- Scripts execute in order after DOM is ready
- **No need for `DOMContentLoaded` wrappers**

### Example: Alert Auto-Dismiss

**Bad (Old Pattern):**
```javascript
// apps/common/static/common/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    // ...
});
```

**Good (Defer Pattern):**
```javascript
// apps/common/static/common/js/main.js
// No wrapper needed - defer ensures DOM is ready
const alerts = document.querySelectorAll('.alert');
alerts.forEach(alert => {
    setTimeout(() => alert.classList.add('fade-out'), 3000);
});
```

## App-Specific Static Files

### Common App (Global)

**CSS:** `apps/common/static/common/css/main.css`
```css
/* Global styles */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.fade-out {
    opacity: 0;
    transition: opacity 0.6s ease-out;
}
```

**JavaScript:** `apps/common/static/common/js/main.js`
```javascript
// Alert auto-dismiss after 3 seconds
const alerts = document.querySelectorAll('.alert');
alerts.forEach(alert => {
    setTimeout(() => {
        alert.classList.add('fade-out');
        setTimeout(() => alert.remove(), 600);
    }, 3000);
});
```

### Questions App

**JavaScript:** `apps/questions/static/questions/js/question_form.js`
```javascript
// Choice management: add, delete, reorder
// No DOMContentLoaded wrapper needed (defer attribute)

const choiceContainer = document.getElementById('choice-container');
const addChoiceBtn = document.getElementById('add-choice-btn');

addChoiceBtn.addEventListener('click', function() {
    // Clone template and append
});

function renumberForms() {
    // Update form indices
}
```

**JavaScript:** `apps/questions/static/questions/js/question_list.js`
```javascript
// Auto-submit filter form on change
const filterForm = document.getElementById('filter-form');
const subjectSelect = document.getElementById('id_subject');

subjectSelect.addEventListener('change', () => filterForm.submit());
```

### Subjects App

**JavaScript:** `apps/subjects/static/subjects/js/subject_tree.js`
```javascript
// Recursive tree expand/collapse
const toggleBtns = document.querySelectorAll('.subject-toggle');

toggleBtns.forEach(btn => {
    btn.addEventListener('click', function() {
        const subtree = this.nextElementSibling;
        subtree.classList.toggle('collapsed');
    });
});
```

## Template Usage Patterns

### Including App-Specific CSS

```django
{% extends 'common/base.html' %}
{% load static %}
{% load compress %}

{% block extra_css %}
    <link rel="stylesheet" href="{% static 'myapp/css/custom.css' %}">
{% endblock %}
```

### Including App-Specific JavaScript

```django
{% block extra_js %}
    <script src="{% static 'myapp/js/custom.js' %}" defer></script>
{% endblock %}
```

**Note:** `defer` attribute is critical - it allows scripts to run without `DOMContentLoaded` wrapper.

## Third-Party Libraries

### Bootstrap 5.3.8

**CDN Link:**
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" 
      rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js" 
        defer></script>
```

**Usage:**
- Grid system for responsive layouts
- Utility classes for spacing, colors, typography
- Components: cards, alerts, modals, forms
- JavaScript components: dropdowns, tooltips, modals

### FontAwesome 7.1.0

**CDN Link:**
```html
<link rel="stylesheet" 
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.1.0/css/all.min.css">
```

**Usage:**
```html
<i class="fas fa-plus"></i>  <!-- Plus icon -->
<i class="fas fa-edit"></i>  <!-- Edit icon -->
<i class="fas fa-trash"></i> <!-- Delete icon -->
```

**Common Icons:**
- `fa-plus`: Add actions
- `fa-edit`: Edit actions
- `fa-trash`: Delete actions
- `fa-arrow-up` / `fa-arrow-down`: Reorder
- `fa-check`: Correct answer indicator

## Deployment Workflow

### Development Mode

```bash
# Static files served directly from app directories
# No compression needed
DEBUG = True
COMPRESS_ENABLED = False
```

Access: `http://localhost:8000/static/common/js/main.js`

### Production Mode

```bash
# 1. Collect all static files
poetry run python manage.py collectstatic --noinput

# 2. Compress CSS/JavaScript
poetry run python manage.py compress

# 3. Generated files in staticfiles/
# - Minified CSS/JavaScript
# - Cache-busted filenames (e.g., main.a1b2c3d4.js)
```

**Result:**
```html
<!-- Development -->
<link rel="stylesheet" href="/static/common/css/main.css">

<!-- Production -->
<link rel="stylesheet" href="/static/CACHE/css/output.a1b2c3d4.css">
```

## Cache-Busting Strategy

### Compressor Hash Naming

Django-compressor automatically generates hash-based filenames:
```
output.{hash}.css
output.{hash}.js
```

**Hash Changes When:**
- File content changes
- Compression settings change

**Browser Behavior:**
- New hash = new URL
- Browser fetches fresh file
- Old cached files ignored

### Static File Versioning

For non-compressed files (images, fonts):
```python
# settings.py
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
```

Generates `staticfiles.json` with hashed filenames.

## Testing Considerations

### Test Static Files

Tests don't require static file collection:
```python
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
```

Django test client serves static files automatically.

### JavaScript Testing

**Current:** Manual testing in browser (defer behavior, DOM manipulation)

**Future:** Consider Jest or Cypress for automated JS testing

## Performance Optimization

### Compression Benefits

**Before Compression:**
```
main.css: 12.5 KB
bootstrap-overrides.css: 3.2 KB
Total: 15.7 KB
```

**After Compression + Minification:**
```
output.a1b2c3d4.css: 8.1 KB (48% reduction)
output.a1b2c3d4.css.gz: 2.3 KB (85% reduction with gzip)
```

### CDN vs Self-Hosted

**Current Strategy:**
- Bootstrap/FontAwesome from CDN (faster initial load, browser caching across sites)
- App-specific files self-hosted (control versioning, offline development)

**Future:** Consider self-hosting all assets for:
- GDPR compliance
- Offline-first PWA support
- Subresource integrity control

## Constraints

### No Global Static Directory

**Prohibited:**
```
qoodle-ui/
└── static/          # ❌ Do not create
    └── css/
```

**Required:**
```
qoodle-ui/
└── apps/
    └── myapp/
        └── static/
            └── myapp/  # ✅ Namespaced by app
                └── css/
```

### App Namespace Requirement

Files must be in `static/appname/` subdirectory:
```
✅ apps/questions/static/questions/js/question_form.js
❌ apps/questions/static/js/question_form.js  # Missing namespace
```

**Rationale:** Prevents file name conflicts between apps.

## Related Specifications

- [001-uuid-model-system](../001-uuid-model-system/spec.md) - Admin interface styling
- [002-subject-hierarchy](../002-subject-hierarchy/spec.md) - Tree UI JavaScript
- [003-multilingual-questions](../003-multilingual-questions/spec.md) - Question form scripts

## Future Enhancements

- Sass/SCSS compilation for advanced CSS
- JavaScript bundling with webpack/vite
- Automated JavaScript testing (Jest/Cypress)
- Progressive Web App (PWA) support
- Service worker for offline access
- Image optimization pipeline
- SVG sprite generation
- Custom icon font

## References

- Django Static Files: https://docs.djangoproject.com/en/6.0/howto/static-files/
- Django Compressor: https://django-compressor.readthedocs.io/
- Bootstrap 5.3: https://getbootstrap.com/docs/5.3/
- FontAwesome 7: https://fontawesome.com/
- Script Defer Attribute: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script#defer
