"""Tests for the subjects app."""

import uuid

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from apps.subjects.models import Subject


class SubjectModelTests(TestCase):
    """Test cases for the Subject model."""

    def test_subject_creation(self):
        """Test creating a basic subject."""
        subject = Subject.objects.create(name="Mathematics", description="Math topics")
        self.assertIsInstance(subject.id, uuid.UUID)
        self.assertEqual(subject.name, "Mathematics")
        self.assertEqual(subject.description, "Math topics")
        self.assertIsNone(subject.parent)
        self.assertIsNotNone(subject.created_at)
        self.assertIsNotNone(subject.updated_at)

    def test_subject_str_representation(self):
        """Test string representation of subject."""
        subject = Subject.objects.create(name="Science")
        self.assertEqual(str(subject), "Science")

    def test_hierarchical_subjects(self):
        """Test creating a parent-child subject hierarchy."""
        parent = Subject.objects.create(name="Mathematics")
        child = Subject.objects.create(name="Algebra", parent=parent)

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.get_children())

    def test_get_ancestors(self):
        """Test retrieving all ancestor subjects."""
        root = Subject.objects.create(name="Mathematics")
        level1 = Subject.objects.create(name="Algebra", parent=root)
        level2 = Subject.objects.create(name="Linear Equations", parent=level1)

        ancestors = level2.get_ancestors()
        self.assertEqual(len(ancestors), 2)
        self.assertEqual(ancestors[0], root)
        self.assertEqual(ancestors[1], level1)

    def test_get_descendants(self):
        """Test retrieving all descendant subjects."""
        root = Subject.objects.create(name="Mathematics")
        child1 = Subject.objects.create(name="Algebra", parent=root)
        child2 = Subject.objects.create(name="Geometry", parent=root)
        grandchild = Subject.objects.create(name="Linear Equations", parent=child1)

        descendants = root.get_descendants()
        self.assertEqual(len(descendants), 3)
        self.assertIn(child1, descendants)
        self.assertIn(child2, descendants)
        self.assertIn(grandchild, descendants)

    def test_depth_property(self):
        """Test depth calculation for nested subjects."""
        root = Subject.objects.create(name="Mathematics")
        level1 = Subject.objects.create(name="Algebra", parent=root)
        level2 = Subject.objects.create(name="Linear Equations", parent=level1)

        self.assertEqual(root.depth, 0)
        self.assertEqual(level1.depth, 1)
        self.assertEqual(level2.depth, 2)

    def test_is_root_property(self):
        """Test is_root property."""
        root = Subject.objects.create(name="Mathematics")
        child = Subject.objects.create(name="Algebra", parent=root)

        self.assertTrue(root.is_root)
        self.assertFalse(child.is_root)

    def test_has_children_method(self):
        """Test has_children method."""
        parent = Subject.objects.create(name="Mathematics")
        child = Subject.objects.create(name="Algebra", parent=parent)

        self.assertTrue(parent.has_children())
        self.assertFalse(child.has_children())

    def test_question_count_placeholder(self):
        """Test that get_question_count returns 0 (placeholder)."""
        subject = Subject.objects.create(name="Mathematics")
        self.assertEqual(subject.get_question_count(), 0)

    def test_unique_constraint_same_parent(self):
        """Test that subjects with same parent must have unique names."""
        parent = Subject.objects.create(name="Mathematics")
        Subject.objects.create(name="Algebra", parent=parent)

        with self.assertRaises(IntegrityError):
            Subject.objects.create(name="Algebra", parent=parent)

    def test_same_name_different_parents_allowed(self):
        """Test that same name is allowed under different parents."""
        parent1 = Subject.objects.create(name="Mathematics")
        parent2 = Subject.objects.create(name="Science")

        child1 = Subject.objects.create(name="Statistics", parent=parent1)
        child2 = Subject.objects.create(name="Statistics", parent=parent2)

        self.assertNotEqual(child1, child2)

    def test_get_full_path(self):
        """Test that get_full_path returns the correct hierarchical path."""
        root = Subject.objects.create(name="Math")
        algebra = Subject.objects.create(name="Algebra", parent=root)
        equations = Subject.objects.create(name="Equations", parent=algebra)

        self.assertEqual(root.get_full_path(), "Math")
        self.assertEqual(algebra.get_full_path(), "Math > Algebra")
        self.assertEqual(equations.get_full_path(), "Math > Algebra > Equations")

    def test_get_full_path_custom_separator(self):
        """Test that get_full_path works with custom separator."""
        root = Subject.objects.create(name="Math")
        algebra = Subject.objects.create(name="Algebra", parent=root)

        self.assertEqual(algebra.get_full_path("/"), "Math/Algebra")
        self.assertEqual(algebra.get_full_path(" :: "), "Math :: Algebra")


class SubjectViewTests(TestCase):
    """Test cases for subject views."""

    def test_subject_list_view(self):
        """Test the subject list view."""
        Subject.objects.create(name="Mathematics")
        Subject.objects.create(name="Science")

        response = self.client.get(reverse("subjects:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "subjects/subject_list.html")
        self.assertContains(response, "Mathematics")
        self.assertContains(response, "Science")

    def test_subject_list_empty(self):
        """Test subject list view with no subjects."""
        response = self.client.get(reverse("subjects:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No subjects yet")

    def test_subject_create_view_get(self):
        """Test GET request to subject create view."""
        response = self.client.get(reverse("subjects:create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "subjects/subject_form.html")
        self.assertContains(response, "Create Subject")

    def test_subject_create_view_post(self):
        """Test POST request to create a new subject."""
        data = {
            "name": "Mathematics",
            "description": "Math topics",
        }
        response = self.client.post(reverse("subjects:create"), data)
        self.assertEqual(response.status_code, 302)  # Redirect after success

        subject = Subject.objects.get(name="Mathematics")
        self.assertEqual(subject.description, "Math topics")

    def test_subject_update_view_get(self):
        """Test GET request to subject update view."""
        subject = Subject.objects.create(name="Mathematics")
        response = self.client.get(reverse("subjects:edit", kwargs={"pk": subject.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "subjects/subject_form.html")
        self.assertContains(response, "Edit Subject")

    def test_subject_update_view_post(self):
        """Test POST request to update a subject."""
        subject = Subject.objects.create(name="Math")
        data = {
            "name": "Mathematics",
            "description": "Updated description",
        }
        response = self.client.post(reverse("subjects:edit", kwargs={"pk": subject.pk}), data)
        self.assertEqual(response.status_code, 302)

        subject.refresh_from_db()
        self.assertEqual(subject.name, "Mathematics")
        self.assertEqual(subject.description, "Updated description")

    def test_subject_delete_view_get(self):
        """Test GET request to subject delete view."""
        subject = Subject.objects.create(name="Mathematics")
        response = self.client.get(reverse("subjects:delete", kwargs={"pk": subject.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "subjects/subject_confirm_delete.html")

    def test_subject_delete_view_post(self):
        """Test POST request to delete a subject."""
        subject = Subject.objects.create(name="Mathematics")
        response = self.client.post(reverse("subjects:delete", kwargs={"pk": subject.pk}))
        self.assertEqual(response.status_code, 302)

        self.assertFalse(Subject.objects.filter(pk=subject.pk).exists())

    def test_subject_delete_with_children_protected(self):
        """Test that subjects with children cannot be deleted."""
        parent = Subject.objects.create(name="Mathematics")
        Subject.objects.create(name="Algebra", parent=parent)

        response = self.client.post(reverse("subjects:delete", kwargs={"pk": parent.pk}))
        # Should still exist because deletion is protected
        self.assertTrue(Subject.objects.filter(pk=parent.pk).exists())

    def test_hierarchical_display(self):
        """Test that hierarchical structure is displayed correctly."""
        parent = Subject.objects.create(name="Mathematics")
        child = Subject.objects.create(name="Algebra", parent=parent)

        response = self.client.get(reverse("subjects:list"))
        self.assertContains(response, "Mathematics")
        self.assertContains(response, "Algebra")


class SubjectFormTests(TestCase):
    """Test cases for subject forms."""

    def test_form_valid_data(self):
        """Test form with valid data."""
        from apps.subjects.forms import SubjectForm

        form = SubjectForm(data={"name": "Mathematics", "description": "Math topics"})
        self.assertTrue(form.is_valid())

    def test_form_missing_required_field(self):
        """Test form with missing required field."""
        from apps.subjects.forms import SubjectForm

        form = SubjectForm(data={"description": "Math topics"})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_form_prevents_circular_reference(self):
        """Test that form prevents setting subject as its own parent."""
        from apps.subjects.forms import SubjectForm

        subject = Subject.objects.create(name="Mathematics")
        child = Subject.objects.create(name="Algebra", parent=subject)

        form = SubjectForm(instance=subject)
        # Subject should not be in its own parent choices
        parent_choices = [choice[0] for choice in form.fields["parent"].choices]
        self.assertNotIn(subject.pk, parent_choices)
