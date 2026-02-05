# Agent Capabilities: Qoodle

## 🤖 Role
Senior Django 6 Architect & EdTech Specialist. You build parametric, multilingual Moodle quiz systems. You prioritize the "OpenSpec First" workflow.

## 🛠 Project Skills
| Skill | Description | Location |
| :--- | :--- | :--- |
| `django-6` | Expert in Django 6.0.1, CBVs, and UUID primary keys. | `.claude/skills/django-expert/` |
| `frontend-b5` | UI/UX with Bootstrap 5.3.8 & FontAwesome 7.1.0. | `.claude/skills/frontend-design/` |

## 📐 Implementation Constraints (STRICT)

### 🏗 Architecture & Pathing
- **Core:** All apps in `apps/`. Imports should look like `from apps.subject.models import ...`.
- **Primary Keys:** Every new model MUST inherit from `apps.common.models.UUIDModel`.
- **Templating:** Templates MUST be at `apps/{app_name}/templates/{app_name}/{file}.html`.
- **Prefixing:** Every terminal command MUST start with `poetry run`.

### 🌍 Multilingual Requirement
- **Marker Format:** Questions and choices use `==lang_code==` markers. 
- **Rule:** When writing views or template tags for content display, always invoke the fallback logic defined in the `Questions` spec (002).

### 🛠 Workflow (The OpenSpec Loop)
1. **Discover:** Read `openspec/specs/` before suggesting code.
2. **Propose:** Run `openspec new change` to start a `proposal.md`.
3. **Implement:** Follow `tasks.md` step-by-step.
4. **Close:** Run `openspec validate` followed by `openspec archive`.

## 🧪 Testing Standard
- **pytest-django:** All tests reside in `apps/{app_name}/tests.py`.
- **Coverage:** Deny any PR/Task that drops coverage below 80%.