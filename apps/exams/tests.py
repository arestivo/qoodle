"""Tests for the exams app."""

from datetime import date, timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from apps.exams.forms import ExamForm
from apps.exams.models import Exam, QuestionPool, QuestionPoolTemplate
from apps.questions.models import QuestionTemplate
from apps.subjects.models import Subject

# ============================================================================
# Phase 5.1: Model Tests
# ============================================================================


class ExamModelTests(TestCase):
    """Test the Exam model."""

    def test_create_exam_with_required_title_only(self):
        """Test creating exam with only required title field."""
        exam = Exam.objects.create(title="Midterm Exam")
        self.assertEqual(exam.title, "Midterm Exam")
        self.assertIsNone(exam.date)
        self.assertEqual(exam.description, "")

    def test_create_exam_with_all_fields(self):
        """Test creating exam with all fields populated."""
        exam_date = date.today() + timedelta(days=7)
        exam = Exam.objects.create(
            title="Final Exam",
            date=exam_date,
            description="Comprehensive final examination",
        )
        self.assertEqual(exam.title, "Final Exam")
        self.assertEqual(exam.date, exam_date)
        self.assertEqual(exam.description, "Comprehensive final examination")

    def test_exam_str_returns_title(self):
        """Test that __str__ returns the exam title."""
        exam = Exam.objects.create(title="Quiz 1")
        self.assertEqual(str(exam), "Quiz 1")

    def test_delete_exam_cascades_to_pools(self):
        """Test that deleting an exam also deletes its pools."""
        exam = Exam.objects.create(title="Test Exam")
        pool1 = QuestionPool.objects.create(exam=exam, order=1)
        pool2 = QuestionPool.objects.create(exam=exam, order=2)

        pool_ids = [pool1.id, pool2.id]
        exam.delete()

        # Verify pools are deleted
        for pool_id in pool_ids:
            self.assertFalse(QuestionPool.objects.filter(id=pool_id).exists())

    def test_delete_exam_does_not_delete_question_templates(self):
        """Test that deleting an exam does not delete question templates."""
        subject = Subject.objects.create(name="Math")
        template = QuestionTemplate.objects.create(
            title="Sample Question",
            subject=subject,
            text="What is 2+2?",
        )

        exam = Exam.objects.create(title="Test Exam")
        pool = QuestionPool.objects.create(exam=exam, order=1)
        QuestionPoolTemplate.objects.create(pool=pool, template=template, number_of_versions=1)

        template_id = template.id
        exam.delete()

        # Verify template still exists
        self.assertTrue(QuestionTemplate.objects.filter(id=template_id).exists())


class QuestionPoolModelTests(TestCase):
    """Test the QuestionPool model."""

    def setUp(self):
        """Set up test fixtures."""
        self.exam1 = Exam.objects.create(title="Exam 1")
        self.exam2 = Exam.objects.create(title="Exam 2")

    def test_create_pool_with_exam_and_order(self):
        """Test creating a pool with exam and order."""
        pool = QuestionPool.objects.create(exam=self.exam1, order=1)
        self.assertEqual(pool.exam, self.exam1)
        self.assertEqual(pool.order, 1)

    def test_unique_constraint_on_exam_order_prevents_duplicates(self):
        """Test that (exam, order) unique constraint prevents duplicates."""
        QuestionPool.objects.create(exam=self.exam1, order=1)

        with self.assertRaises(IntegrityError):
            QuestionPool.objects.create(exam=self.exam1, order=1)

    def test_same_order_allowed_in_different_exams(self):
        """Test that same order is allowed in different exams."""
        pool1 = QuestionPool.objects.create(exam=self.exam1, order=1)
        pool2 = QuestionPool.objects.create(exam=self.exam2, order=1)

        self.assertEqual(pool1.order, pool2.order)
        self.assertNotEqual(pool1.exam, pool2.exam)

    def test_delete_pool_unlinks_templates_not_delete(self):
        """Test that deleting a pool unlinks templates but doesn't delete them."""
        subject = Subject.objects.create(name="Science")
        template = QuestionTemplate.objects.create(
            title="Test Question",
            subject=subject,
            text="Sample text",
        )

        pool = QuestionPool.objects.create(exam=self.exam1, order=1)
        QuestionPoolTemplate.objects.create(pool=pool, template=template, number_of_versions=1)

        template_id = template.id
        pool.delete()

        # Verify template still exists
        self.assertTrue(QuestionTemplate.objects.filter(id=template_id).exists())

    def test_pool_ordering_by_order_field(self):
        """Test that pools are ordered by the order field."""
        pool3 = QuestionPool.objects.create(exam=self.exam1, order=3)
        pool1 = QuestionPool.objects.create(exam=self.exam1, order=1)
        pool2 = QuestionPool.objects.create(exam=self.exam1, order=2)

        pools = list(self.exam1.pools.all())
        self.assertEqual(pools, [pool1, pool2, pool3])


class QuestionPoolTemplateModelTests(TestCase):
    """Test the QuestionPoolTemplate model."""

    def setUp(self):
        """Set up test fixtures."""
        self.exam = Exam.objects.create(title="Test Exam")
        self.pool = QuestionPool.objects.create(exam=self.exam, order=1)
        self.subject = Subject.objects.create(name="Physics")
        self.template1 = QuestionTemplate.objects.create(
            title="Question 1",
            subject=self.subject,
            text="Question text 1",
        )
        self.template2 = QuestionTemplate.objects.create(
            title="Question 2",
            subject=self.subject,
            text="Question text 2",
        )

    def test_create_pool_template_link_with_version_count(self):
        """Test creating a pool-template link with version count."""
        pt = QuestionPoolTemplate.objects.create(
            pool=self.pool, template=self.template1, number_of_versions=5
        )
        self.assertEqual(pt.pool, self.pool)
        self.assertEqual(pt.template, self.template1)
        self.assertEqual(pt.number_of_versions, 5)

    def test_unique_constraint_on_pool_template_prevents_duplicates(self):
        """Test that (pool, template) unique constraint prevents duplicates."""
        QuestionPoolTemplate.objects.create(
            pool=self.pool, template=self.template1, number_of_versions=1
        )

        with self.assertRaises(IntegrityError):
            QuestionPoolTemplate.objects.create(
                pool=self.pool, template=self.template1, number_of_versions=1
            )

    def test_same_template_can_be_in_different_pools(self):
        """Test that same template can be in different pools."""
        pool2 = QuestionPool.objects.create(exam=self.exam, order=2)

        pt1 = QuestionPoolTemplate.objects.create(
            pool=self.pool, template=self.template1, number_of_versions=1
        )
        pt2 = QuestionPoolTemplate.objects.create(
            pool=pool2, template=self.template1, number_of_versions=3
        )

        self.assertEqual(pt1.template, pt2.template)
        self.assertNotEqual(pt1.pool, pt2.pool)

    def test_validation_fails_if_number_of_versions_less_than_1(self):
        """Test that validation fails if number_of_versions < 1."""
        from django.core.exceptions import ValidationError

        pt = QuestionPoolTemplate(pool=self.pool, template=self.template1, number_of_versions=0)
        with self.assertRaises(ValidationError):
            pt.full_clean()

    def test_default_number_of_versions_is_1(self):
        """Test that default number_of_versions is 1."""
        pt = QuestionPoolTemplate.objects.create(pool=self.pool, template=self.template1)
        self.assertEqual(pt.number_of_versions, 1)


# ============================================================================
# Phase 5.2: View Tests
# ============================================================================


class ExamViewTests(TestCase):
    """Test exam views."""

    def setUp(self):
        """Set up test fixtures."""
        self.exam1 = Exam.objects.create(title="Exam 1")
        self.exam2 = Exam.objects.create(title="Exam 2")

    def test_exam_list_view_returns_200_status(self):
        """Test that exam list view returns 200 status."""
        response = self.client.get(reverse("exams:list"))
        self.assertEqual(response.status_code, 200)

    def test_exam_list_displays_all_exams(self):
        """Test that exam list displays all exams."""
        response = self.client.get(reverse("exams:list"))
        self.assertContains(response, "Exam 1")
        self.assertContains(response, "Exam 2")

    def test_exam_list_pagination_works(self):
        """Test that exam list pagination works correctly."""
        # Create 25 exams to trigger pagination (20 per page)
        for i in range(3, 28):
            Exam.objects.create(title=f"Exam {i}")

        response = self.client.get(reverse("exams:list"))
        self.assertEqual(len(response.context["exams"]), 20)

        # Check page 2
        response = self.client.get(reverse("exams:list") + "?page=2")
        self.assertEqual(len(response.context["exams"]), 7)

    def test_exam_create_view_get_returns_form(self):
        """Test that exam create GET returns form."""
        response = self.client.get(reverse("exams:create"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_exam_create_post_with_valid_data_creates_exam(self):
        """Test that exam create POST with valid data creates exam."""
        data = {"title": "New Exam", "description": "Test description"}
        response = self.client.post(reverse("exams:create"), data)

        self.assertTrue(Exam.objects.filter(title="New Exam").exists())
        exam = Exam.objects.get(title="New Exam")
        self.assertRedirects(response, reverse("exams:detail", kwargs={"pk": exam.pk}))

    def test_exam_create_post_with_missing_title_fails_validation(self):
        """Test that exam create POST with missing title fails validation."""
        data = {"description": "Test description"}
        response = self.client.post(reverse("exams:create"), data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Exam.objects.filter(description="Test description").exists())
        self.assertFormError(response.context["form"], "title", "This field is required.")

    def test_exam_detail_view_displays_exam_and_pools(self):
        """Test that exam detail view displays exam and its pools."""
        QuestionPool.objects.create(exam=self.exam1, order=1)
        response = self.client.get(reverse("exams:detail", kwargs={"pk": self.exam1.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Exam 1")
        self.assertIn("pools", response.context)

    def test_exam_update_view_prepopulates_form(self):
        """Test that exam update view pre-populates form."""
        response = self.client.get(reverse("exams:edit", kwargs={"pk": self.exam1.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].instance, self.exam1)

    def test_exam_update_post_saves_changes(self):
        """Test that exam update POST saves changes."""
        data = {"title": "Updated Exam", "description": "Updated description"}
        self.client.post(reverse("exams:edit", kwargs={"pk": self.exam1.pk}), data)

        self.exam1.refresh_from_db()
        self.assertEqual(self.exam1.title, "Updated Exam")
        self.assertEqual(self.exam1.description, "Updated description")

    def test_exam_delete_view_shows_confirmation(self):
        """Test that exam delete view shows confirmation."""
        response = self.client.get(reverse("exams:delete", kwargs={"pk": self.exam1.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Exam 1")

    def test_exam_delete_post_deletes_exam(self):
        """Test that exam delete POST deletes exam."""
        exam_id = self.exam1.id
        response = self.client.post(reverse("exams:delete", kwargs={"pk": self.exam1.pk}))

        self.assertFalse(Exam.objects.filter(id=exam_id).exists())
        self.assertRedirects(response, reverse("exams:list"))


class PoolViewTests(TestCase):
    """Test pool views."""

    def setUp(self):
        """Set up test fixtures."""
        self.exam = Exam.objects.create(title="Test Exam")

    def test_pool_create_adds_pool_with_correct_order(self):
        """Test that pool create adds pool with correct order."""
        self.client.get(reverse("exams:pool_create", kwargs={"exam_pk": self.exam.pk}))

        pool = QuestionPool.objects.filter(exam=self.exam).first()
        self.assertIsNotNone(pool)
        self.assertEqual(pool.order, 1)

    def test_pool_create_with_existing_pools_sets_order_max_plus_1(self):
        """Test that pool create with existing pools sets order = max + 1."""
        QuestionPool.objects.create(exam=self.exam, order=1)
        QuestionPool.objects.create(exam=self.exam, order=2)

        self.client.get(reverse("exams:pool_create", kwargs={"exam_pk": self.exam.pk}))

        pool = QuestionPool.objects.filter(exam=self.exam, order=3).first()
        self.assertIsNotNone(pool)

    def test_pool_delete_removes_pool(self):
        """Test that pool delete removes pool."""
        pool = QuestionPool.objects.create(exam=self.exam, order=1)
        pool_id = pool.id

        self.client.post(
            reverse("exams:pool_delete", kwargs={"exam_pk": self.exam.pk, "pk": pool.pk})
        )

        self.assertFalse(QuestionPool.objects.filter(id=pool_id).exists())

    def test_pool_delete_does_not_delete_templates(self):
        """Test that pool delete does not delete templates."""
        subject = Subject.objects.create(name="Math")
        template = QuestionTemplate.objects.create(
            title="Test Question",
            subject=subject,
            text="Question text",
        )

        pool = QuestionPool.objects.create(exam=self.exam, order=1)
        QuestionPoolTemplate.objects.create(pool=pool, template=template, number_of_versions=1)

        template_id = template.id
        self.client.post(
            reverse("exams:pool_delete", kwargs={"exam_pk": self.exam.pk, "pk": pool.pk})
        )

        self.assertTrue(QuestionTemplate.objects.filter(id=template_id).exists())


class PoolTemplateViewTests(TestCase):
    """Test pool template views."""

    def setUp(self):
        """Set up test fixtures."""
        self.exam = Exam.objects.create(title="Test Exam")
        self.pool = QuestionPool.objects.create(exam=self.exam, order=1)
        self.subject = Subject.objects.create(name="Science")
        self.template1 = QuestionTemplate.objects.create(
            title="Template 1",
            subject=self.subject,
            text="Question 1",
        )
        self.template2 = QuestionTemplate.objects.create(
            title="Template 2",
            subject=self.subject,
            text="Question 2",
        )

    def test_pool_template_add_view_excludes_existing_templates(self):
        """Test that pool template add view excludes already-used templates."""
        # Add template1 to pool
        QuestionPoolTemplate.objects.create(
            pool=self.pool, template=self.template1, number_of_versions=1
        )

        response = self.client.get(
            reverse(
                "exams:pool_template_add",
                kwargs={"exam_pk": self.exam.pk, "pool_pk": self.pool.pk},
            )
        )

        available_templates = response.context["available_templates"]
        template_ids = [t.id for t in available_templates]

        self.assertNotIn(self.template1.id, template_ids)
        self.assertIn(self.template2.id, template_ids)

    def test_pool_template_add_post_saves_multiple_templates(self):
        """Test that pool template add can save multiple templates at once."""
        data = {
            "templates": [str(self.template1.id), str(self.template2.id)],
            "default_versions": "3",
        }

        self.client.post(
            reverse(
                "exams:pool_template_add",
                kwargs={"exam_pk": self.exam.pk, "pool_pk": self.pool.pk},
            ),
            data,
        )

        self.assertTrue(
            QuestionPoolTemplate.objects.filter(pool=self.pool, template=self.template1).exists()
        )
        self.assertTrue(
            QuestionPoolTemplate.objects.filter(pool=self.pool, template=self.template2).exists()
        )

    def test_pool_template_delete_removes_link(self):
        """Test that pool template delete removes the link."""
        pt = QuestionPoolTemplate.objects.create(
            pool=self.pool, template=self.template1, number_of_versions=1
        )
        pt_id = pt.id

        self.client.post(
            reverse(
                "exams:pool_template_delete",
                kwargs={"exam_pk": self.exam.pk, "pool_pk": self.pool.pk, "pk": pt.pk},
            )
        )

        self.assertFalse(QuestionPoolTemplate.objects.filter(id=pt_id).exists())

    def test_pool_reorder_up_swaps_with_previous(self):
        """Test reordering a pool up swaps with the previous pool."""
        pool2 = QuestionPool.objects.create(exam=self.exam, order=2)

        response = self.client.post(
            reverse("exams:pool_reorder", kwargs={"exam_pk": self.exam.pk, "pk": pool2.pk}),
            {"direction": "up"},
        )

        self.assertEqual(response.status_code, 302)
        self.pool.refresh_from_db()
        pool2.refresh_from_db()
        self.assertEqual(self.pool.order, 2)
        self.assertEqual(pool2.order, 1)

    def test_pool_reorder_down_swaps_with_next(self):
        """Test reordering a pool down swaps with the next pool."""
        pool2 = QuestionPool.objects.create(exam=self.exam, order=2)

        response = self.client.post(
            reverse("exams:pool_reorder", kwargs={"exam_pk": self.exam.pk, "pk": self.pool.pk}),
            {"direction": "down"},
        )

        self.assertEqual(response.status_code, 302)
        self.pool.refresh_from_db()
        pool2.refresh_from_db()
        self.assertEqual(self.pool.order, 2)
        self.assertEqual(pool2.order, 1)

    def test_pool_reorder_invalid_direction_redirects(self):
        """Test reordering with invalid direction still redirects (no-op)."""
        response = self.client.post(
            reverse("exams:pool_reorder", kwargs={"exam_pk": self.exam.pk, "pk": self.pool.pk}),
            {"direction": "invalid"},
        )

        self.assertEqual(response.status_code, 302)
        self.pool.refresh_from_db()
        self.assertEqual(self.pool.order, 1)  # Order unchanged


# ============================================================================
# Phase 5.3: Form Tests
# ============================================================================


class ExamFormTests(TestCase):
    """Test the ExamForm."""

    def test_exam_form_with_valid_data_is_valid(self):
        """Test that ExamForm with valid data is valid."""
        form_data = {"title": "Test Exam", "description": "Test description"}
        form = ExamForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_exam_form_with_missing_title_is_invalid(self):
        """Test that ExamForm with missing title is invalid."""
        form_data = {"description": "Test description"}
        form = ExamForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_exam_form_accepts_optional_date_and_description(self):
        """Test that ExamForm accepts optional date and description."""
        form_data = {"title": "Test Exam"}
        form = ExamForm(data=form_data)
        self.assertTrue(form.is_valid())

        exam_date = date.today() + timedelta(days=7)
        form_data = {"title": "Test Exam", "date": exam_date, "description": "Description"}
        form = ExamForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_exam_form_date_validation_future_dates_allowed(self):
        """Test that ExamForm allows future dates."""
        future_date = date.today() + timedelta(days=30)
        form_data = {"title": "Future Exam", "date": future_date}
        form = ExamForm(data=form_data)
        self.assertTrue(form.is_valid())


# ============================================================================
# Phase 5.4: Integration Tests
# ============================================================================


class ExamWorkflowIntegrationTests(TestCase):
    """Integration tests for exam workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.subject = Subject.objects.create(name="Math")
        self.templates = [
            QuestionTemplate.objects.create(
                title=f"Question {i}",
                subject=self.subject,
                text=f"Question text {i}",
            )
            for i in range(1, 7)
        ]

    def test_full_workflow_create_exam_add_pool_add_templates_view_detail(self):
        """Test full workflow: create exam, add pool, add templates, view detail."""
        # Create exam
        response = self.client.post(reverse("exams:create"), {"title": "Integration Test Exam"})
        exam = Exam.objects.get(title="Integration Test Exam")
        self.assertRedirects(response, reverse("exams:detail", kwargs={"pk": exam.pk}))

        # Add pool
        self.client.get(reverse("exams:pool_create", kwargs={"exam_pk": exam.pk}))
        pool = QuestionPool.objects.get(exam=exam, order=1)

        # Add templates to pool
        data = {
            "templates": [str(self.templates[0].id), str(self.templates[1].id)],
            "default_versions": "5",
        }
        self.client.post(
            reverse(
                "exams:pool_template_add",
                kwargs={"exam_pk": exam.pk, "pool_pk": pool.pk},
            ),
            data,
        )

        # View detail
        response = self.client.get(reverse("exams:detail", kwargs={"pk": exam.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Integration Test Exam")

    def test_create_exam_with_3_pools_each_with_2_templates(self):
        """Test creating exam with 3 pools, each with 2 templates."""
        exam = Exam.objects.create(title="Multi-Pool Exam")

        for i in range(1, 4):
            pool = QuestionPool.objects.create(exam=exam, order=i)
            QuestionPoolTemplate.objects.create(
                pool=pool, template=self.templates[(i - 1) * 2], number_of_versions=3
            )
            QuestionPoolTemplate.objects.create(
                pool=pool, template=self.templates[(i - 1) * 2 + 1], number_of_versions=3
            )

        self.assertEqual(exam.pools.count(), 3)
        for pool in exam.pools.all():
            self.assertEqual(pool.pool_templates.count(), 2)

    def test_add_same_template_to_different_pools_succeeds(self):
        """Test that adding same template to different pools succeeds."""
        exam = Exam.objects.create(title="Test Exam")
        pool1 = QuestionPool.objects.create(exam=exam, order=1)
        pool2 = QuestionPool.objects.create(exam=exam, order=2)

        template = self.templates[0]

        pt1 = QuestionPoolTemplate.objects.create(
            pool=pool1, template=template, number_of_versions=1
        )
        pt2 = QuestionPoolTemplate.objects.create(
            pool=pool2, template=template, number_of_versions=1
        )

        self.assertEqual(pt1.template, pt2.template)
        self.assertNotEqual(pt1.pool, pt2.pool)

    def test_delete_exam_deletes_pools_but_not_templates(self):
        """Test that deleting exam deletes pools but not templates."""
        exam = Exam.objects.create(title="Test Exam")
        pool = QuestionPool.objects.create(exam=exam, order=1)
        template = self.templates[0]
        QuestionPoolTemplate.objects.create(pool=pool, template=template, number_of_versions=1)

        pool_id = pool.id
        template_id = template.id
        exam.delete()

        self.assertFalse(QuestionPool.objects.filter(id=pool_id).exists())
        self.assertTrue(QuestionTemplate.objects.filter(id=template_id).exists())
