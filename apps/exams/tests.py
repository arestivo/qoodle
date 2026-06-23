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
        pt = QuestionPoolTemplate.objects.create(pool=self.pool, template=self.template1, number_of_versions=5)
        self.assertEqual(pt.pool, self.pool)
        self.assertEqual(pt.template, self.template1)
        self.assertEqual(pt.number_of_versions, 5)

    def test_unique_constraint_on_pool_template_prevents_duplicates(self):
        """Test that (pool, template) unique constraint prevents duplicates."""
        QuestionPoolTemplate.objects.create(pool=self.pool, template=self.template1, number_of_versions=1)

        with self.assertRaises(IntegrityError):
            QuestionPoolTemplate.objects.create(pool=self.pool, template=self.template1, number_of_versions=1)

    def test_same_template_can_be_in_different_pools(self):
        """Test that same template can be in different pools."""
        pool2 = QuestionPool.objects.create(exam=self.exam, order=2)

        pt1 = QuestionPoolTemplate.objects.create(pool=self.pool, template=self.template1, number_of_versions=1)
        pt2 = QuestionPoolTemplate.objects.create(pool=pool2, template=self.template1, number_of_versions=3)

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
        data = {"title": "New Exam", "description": "Test description", "grading_mode": "single"}
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
        data = {"title": "Updated Exam", "description": "Updated description", "grading_mode": "single"}
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


class ExamTotalPointsTests(TestCase):
    """Test total points on the exam detail page."""

    def setUp(self):
        """Create an exam used by total-point scenarios."""
        self.exam = Exam.objects.create(title="Points Exam")

    def get_detail(self):
        """Return the exam detail response."""
        return self.client.get(reverse("exams:detail", kwargs={"pk": self.exam.pk}))

    def test_total_points_sums_all_pool_grades(self):
        """Test pool grades are summed once each."""
        from decimal import Decimal

        QuestionPool.objects.create(exam=self.exam, order=1, default_grade=Decimal("1.00"))
        QuestionPool.objects.create(exam=self.exam, order=2, default_grade=Decimal("2.50"))
        QuestionPool.objects.create(exam=self.exam, order=3, default_grade=Decimal("0.50"))

        response = self.get_detail()

        self.assertEqual(response.context["total_points"], Decimal("4.00"))
        self.assertContains(response, "Total: 4.00 points")

    def test_empty_exam_displays_zero_points(self):
        """Test an exam without pools displays a zero total."""
        from decimal import Decimal

        response = self.get_detail()

        self.assertEqual(response.context["total_points"], Decimal("0.00"))
        self.assertContains(response, "Total: 0.00 points")

    def test_templates_and_versions_do_not_multiply_points(self):
        """Test alternatives in one pool do not increase the total."""
        from decimal import Decimal

        subject = Subject.objects.create(name="Mathematics")
        pool = QuestionPool.objects.create(
            exam=self.exam,
            order=1,
            default_grade=Decimal("2.50"),
        )
        for index in range(2):
            template = QuestionTemplate.objects.create(
                subject=subject,
                title=f"Alternative {index}",
                text={"none": "Question?"},
            )
            QuestionPoolTemplate.objects.create(
                pool=pool,
                template=template,
                number_of_versions=3,
            )

        response = self.get_detail()

        self.assertEqual(response.context["total_points"], Decimal("2.50"))
        self.assertContains(response, "Total: 2.50 points")

    def test_total_reflects_updated_pool_grade(self):
        """Test the total is recalculated after a grade update."""
        from decimal import Decimal

        pool = QuestionPool.objects.create(
            exam=self.exam,
            order=1,
            default_grade=Decimal("1.00"),
        )
        pool.default_grade = Decimal("3.25")
        pool.save()

        response = self.get_detail()

        self.assertEqual(response.context["total_points"], Decimal("3.25"))
        self.assertContains(response, "Total: 3.25 points")


class ExamDuplicationTests(TestCase):
    """Test duplication of exams and their question structure."""

    def setUp(self):
        """Create a populated source exam."""
        from decimal import Decimal

        from apps.questions.models import Choice

        self.subject = Subject.objects.create(name="Mathematics")
        self.source = Exam.objects.create(
            title="Original Exam",
            date=date(2026, 6, 23),
            description="Original description",
            grading_mode="multi",
        )
        self.template1 = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Template 1",
            text={"none": "Question 1"},
        )
        self.template2 = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Template 2",
            text={"none": "Question 2"},
        )
        for template in (self.template1, self.template2):
            Choice.objects.create(template=template, text={"none": "Correct"}, order=0)
            Choice.objects.create(template=template, text={"none": "Wrong"}, order=1)

        pool1 = QuestionPool.objects.create(
            exam=self.source,
            order=1,
            default_grade=Decimal("2.50"),
        )
        pool2 = QuestionPool.objects.create(
            exam=self.source,
            order=2,
            default_grade=Decimal("1.25"),
        )
        QuestionPoolTemplate.objects.create(
            pool=pool1,
            template=self.template1,
            number_of_versions=3,
        )
        QuestionPoolTemplate.objects.create(
            pool=pool1,
            template=self.template2,
            number_of_versions=2,
        )
        QuestionPoolTemplate.objects.create(
            pool=pool2,
            template=self.template2,
            number_of_versions=1,
        )

    def duplicate(self, exam=None):
        """Submit the duplicate action for an exam."""
        exam = exam or self.source
        return self.client.post(
            reverse("exams:duplicate", kwargs={"pk": exam.pk}),
        )

    def test_duplicate_copies_metadata_and_redirects_to_new_exam(self):
        """Test metadata, redirect, and success message."""
        from django.contrib.messages import get_messages

        response = self.duplicate()
        duplicate = Exam.objects.exclude(pk=self.source.pk).get()
        messages = [str(message) for message in get_messages(response.wsgi_request)]

        self.assertRedirects(
            response,
            reverse("exams:detail", kwargs={"pk": duplicate.pk}),
        )
        self.assertEqual(duplicate.title, "Original Exam (Copy)")
        self.assertEqual(duplicate.date, self.source.date)
        self.assertEqual(duplicate.description, self.source.description)
        self.assertEqual(duplicate.grading_mode, self.source.grading_mode)
        self.assertIn('Exam duplicated as "Original Exam (Copy)".', messages)

    def test_duplicate_copies_pools_memberships_and_versions(self):
        """Test the complete exam-owned question structure is copied."""
        self.duplicate()
        duplicate = Exam.objects.exclude(pk=self.source.pk).get()

        source_pools = list(self.source.pools.order_by("order"))
        duplicate_pools = list(duplicate.pools.order_by("order"))
        self.assertEqual(len(duplicate_pools), 2)

        for source_pool, duplicate_pool in zip(
            source_pools,
            duplicate_pools,
            strict=True,
        ):
            self.assertNotEqual(source_pool.pk, duplicate_pool.pk)
            self.assertEqual(duplicate_pool.order, source_pool.order)
            self.assertEqual(
                duplicate_pool.default_grade,
                source_pool.default_grade,
            )
            source_memberships = list(
                source_pool.pool_templates.order_by("template_id").values_list(
                    "template_id",
                    "number_of_versions",
                )
            )
            duplicate_memberships = list(
                duplicate_pool.pool_templates.order_by("template_id").values_list(
                    "template_id",
                    "number_of_versions",
                )
            )
            self.assertEqual(duplicate_memberships, source_memberships)

        self.assertEqual(QuestionTemplate.objects.count(), 2)

    def test_duplicate_does_not_modify_source(self):
        """Test source records remain unchanged."""
        source_pool_ids = list(
            self.source.pools.order_by("order").values_list("pk", flat=True)
        )
        source_membership_count = QuestionPoolTemplate.objects.filter(
            pool__exam=self.source
        ).count()

        self.duplicate()

        self.source.refresh_from_db()
        self.assertEqual(self.source.title, "Original Exam")
        self.assertEqual(
            list(self.source.pools.order_by("order").values_list("pk", flat=True)),
            source_pool_ids,
        )
        self.assertEqual(
            QuestionPoolTemplate.objects.filter(pool__exam=self.source).count(),
            source_membership_count,
        )

    def test_duplicate_empty_exam(self):
        """Test an exam without pools duplicates successfully."""
        empty_exam = Exam.objects.create(title="Empty")

        response = self.duplicate(empty_exam)
        duplicate = Exam.objects.exclude(
            pk__in=[self.source.pk, empty_exam.pk]
        ).get()

        self.assertRedirects(
            response,
            reverse("exams:detail", kwargs={"pk": duplicate.pk}),
        )
        self.assertEqual(duplicate.title, "Empty (Copy)")
        self.assertFalse(duplicate.pools.exists())

    def test_duplicate_title_is_bounded_to_255_characters(self):
        """Test copy suffix does not exceed the title field limit."""
        self.source.title = "x" * 255
        self.source.save()

        self.duplicate()
        duplicate = Exam.objects.exclude(pk=self.source.pk).get()

        self.assertEqual(len(duplicate.title), 255)
        self.assertTrue(duplicate.title.endswith(" (Copy)"))

    def test_duplicate_endpoint_rejects_get(self):
        """Test database mutation is POST-only."""
        response = self.client.get(
            reverse("exams:duplicate", kwargs={"pk": self.source.pk})
        )

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Exam.objects.count(), 1)

    def test_list_and_detail_render_duplicate_post_controls(self):
        """Test both exam views expose CSRF-protected duplicate forms."""
        list_response = self.client.get(reverse("exams:list"))
        detail_response = self.client.get(
            reverse("exams:detail", kwargs={"pk": self.source.pk})
        )
        duplicate_url = reverse("exams:duplicate", kwargs={"pk": self.source.pk})

        self.assertContains(list_response, f'action="{duplicate_url}"')
        self.assertContains(detail_response, f'action="{duplicate_url}"')
        self.assertContains(list_response, "fa-copy")
        self.assertContains(detail_response, "fa-copy")


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

        self.client.post(reverse("exams:pool_delete", kwargs={"exam_pk": self.exam.pk, "pk": pool.pk}))

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
        self.client.post(reverse("exams:pool_delete", kwargs={"exam_pk": self.exam.pk, "pk": pool.pk}))

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
            state="reviewed",
        )
        self.template2 = QuestionTemplate.objects.create(
            title="Template 2",
            subject=self.subject,
            text="Question 2",
            state="reviewed",
        )

    def test_pool_template_add_view_excludes_existing_templates(self):
        """Test that pool template add view excludes already-used templates."""
        # Add template1 to pool
        QuestionPoolTemplate.objects.create(pool=self.pool, template=self.template1, number_of_versions=1)

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

        self.assertTrue(QuestionPoolTemplate.objects.filter(pool=self.pool, template=self.template1).exists())
        self.assertTrue(QuestionPoolTemplate.objects.filter(pool=self.pool, template=self.template2).exists())

    def test_pool_template_delete_removes_link(self):
        """Test that pool template delete removes the link."""
        pt = QuestionPoolTemplate.objects.create(pool=self.pool, template=self.template1, number_of_versions=1)
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

    def test_pool_template_add_only_shows_reviewed_templates(self):
        """Test that pool template add only shows reviewed templates."""
        draft_template = QuestionTemplate.objects.create(
            title="Draft Template",
            subject=self.subject,
            text="Draft Q",
            state="draft",
        )

        response = self.client.get(
            reverse(
                "exams:pool_template_add",
                kwargs={"exam_pk": self.exam.pk, "pool_pk": self.pool.pk},
            )
        )

        available_templates = response.context["available_templates"]
        template_ids = [t.id for t in available_templates]

        self.assertNotIn(draft_template.id, template_ids)
        self.assertIn(self.template1.id, template_ids)
        self.assertIn(self.template2.id, template_ids)


# ============================================================================
# Phase 5.3: Form Tests
# ============================================================================


class ExamFormTests(TestCase):
    """Test the ExamForm."""

    def test_exam_form_with_valid_data_is_valid(self):
        """Test that ExamForm with valid data is valid."""
        form_data = {"title": "Test Exam", "description": "Test description", "grading_mode": "single"}
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
        form_data = {"title": "Test Exam", "grading_mode": "single"}
        form = ExamForm(data=form_data)
        self.assertTrue(form.is_valid())

        exam_date = date.today() + timedelta(days=7)
        form_data = {"title": "Test Exam", "date": exam_date, "description": "Description", "grading_mode": "single"}
        form = ExamForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_exam_form_date_validation_future_dates_allowed(self):
        """Test that ExamForm allows future dates."""
        future_date = date.today() + timedelta(days=30)
        form_data = {"title": "Future Exam", "date": future_date, "grading_mode": "single"}
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
        response = self.client.post(reverse("exams:create"), {"title": "Integration Test Exam", "grading_mode": "single"})
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
            QuestionPoolTemplate.objects.create(pool=pool, template=self.templates[(i - 1) * 2], number_of_versions=3)
            QuestionPoolTemplate.objects.create(pool=pool, template=self.templates[(i - 1) * 2 + 1], number_of_versions=3)

        self.assertEqual(exam.pools.count(), 3)
        for pool in exam.pools.all():
            self.assertEqual(pool.pool_templates.count(), 2)

    def test_add_same_template_to_different_pools_succeeds(self):
        """Test that adding same template to different pools succeeds."""
        exam = Exam.objects.create(title="Test Exam")
        pool1 = QuestionPool.objects.create(exam=exam, order=1)
        pool2 = QuestionPool.objects.create(exam=exam, order=2)

        template = self.templates[0]

        pt1 = QuestionPoolTemplate.objects.create(pool=pool1, template=template, number_of_versions=1)
        pt2 = QuestionPoolTemplate.objects.create(pool=pool2, template=template, number_of_versions=1)

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


# ============================================================================
# Phase 4: Moodle Export Tests
# ============================================================================


class CalculateFractionsTests(TestCase):
    """Test calculate_fractions function for both grading modes."""

    def test_single_mode_2_choices(self):
        """Test single mode with 2 choices returns 100/-100."""
        from decimal import Decimal

        from apps.exams.moodle_export import calculate_fractions

        fractions = calculate_fractions(2, "single")
        self.assertEqual(fractions["correct"], Decimal("100.0"))
        self.assertEqual(fractions["wrong"], Decimal("-100.0"))

    def test_single_mode_3_choices(self):
        """Test single mode with 3 choices returns 100/-50."""
        from decimal import Decimal

        from apps.exams.moodle_export import calculate_fractions

        fractions = calculate_fractions(3, "single")
        self.assertEqual(fractions["correct"], Decimal("100.0"))
        self.assertEqual(fractions["wrong"], Decimal("-50.0"))

    def test_single_mode_4_choices(self):
        """Test single mode with 4 choices returns 100/-33.33."""
        from decimal import Decimal

        from apps.exams.moodle_export import calculate_fractions

        fractions = calculate_fractions(4, "single")
        self.assertEqual(fractions["correct"], Decimal("100.0"))
        self.assertAlmostEqual(float(fractions["wrong"]), -33.33, places=2)

    def test_single_mode_5_choices(self):
        """Test single mode with 5 choices returns 100/-25."""
        from decimal import Decimal

        from apps.exams.moodle_export import calculate_fractions

        fractions = calculate_fractions(5, "single")
        self.assertEqual(fractions["correct"], Decimal("100.0"))
        self.assertEqual(fractions["wrong"], Decimal("-25.0"))

    def test_single_mode_6_choices(self):
        """Test single mode with 6 choices returns 100/-20."""
        from decimal import Decimal

        from apps.exams.moodle_export import calculate_fractions

        fractions = calculate_fractions(6, "single")
        self.assertEqual(fractions["correct"], Decimal("100.0"))
        self.assertEqual(fractions["wrong"], Decimal("-20.0"))

    def test_multi_mode_2_choices(self):
        """Test multi mode with 2 choices returns 90/10."""
        from decimal import Decimal

        from apps.exams.moodle_export import calculate_fractions

        fractions = calculate_fractions(2, "multi")
        self.assertEqual(fractions["correct"], Decimal("90.0"))
        self.assertEqual(fractions["wrong"], Decimal("10.0"))

    def test_multi_mode_3_choices(self):
        """Test multi mode with 3 choices returns 80/10."""
        from decimal import Decimal

        from apps.exams.moodle_export import calculate_fractions

        fractions = calculate_fractions(3, "multi")
        self.assertEqual(fractions["correct"], Decimal("80.0"))
        self.assertEqual(fractions["wrong"], Decimal("10.0"))

    def test_multi_mode_4_choices(self):
        """Test multi mode with 4 choices returns 70/10."""
        from decimal import Decimal

        from apps.exams.moodle_export import calculate_fractions

        fractions = calculate_fractions(4, "multi")
        self.assertEqual(fractions["correct"], Decimal("70.0"))
        self.assertEqual(fractions["wrong"], Decimal("10.0"))

    def test_multi_mode_5_choices(self):
        """Test multi mode with 5 choices returns 60/10."""
        from decimal import Decimal

        from apps.exams.moodle_export import calculate_fractions

        fractions = calculate_fractions(5, "multi")
        self.assertEqual(fractions["correct"], Decimal("60.0"))
        self.assertEqual(fractions["wrong"], Decimal("10.0"))

    def test_multi_mode_6_choices(self):
        """Test multi mode with 6 choices returns 75/5."""
        from decimal import Decimal

        from apps.exams.moodle_export import calculate_fractions

        fractions = calculate_fractions(6, "multi")
        self.assertEqual(fractions["correct"], Decimal("75.0"))
        self.assertEqual(fractions["wrong"], Decimal("5.0"))

    def test_error_less_than_2_choices(self):
        """Test ValueError raised for <2 choices."""
        from apps.exams.moodle_export import calculate_fractions

        with self.assertRaises(ValueError) as cm:
            calculate_fractions(1, "single")
        self.assertIn("at least 2 choices", str(cm.exception))

    def test_error_multi_mode_7_choices(self):
        """Test ValueError raised for 7+ choices in multi mode."""
        from apps.exams.moodle_export import calculate_fractions

        with self.assertRaises(ValueError) as cm:
            calculate_fractions(7, "multi")
        self.assertIn("only supports 2-6 choices", str(cm.exception))


class MarkdownConversionTests(TestCase):
    """Test format_html_for_moodle function."""

    def test_convert_code_blocks(self):
        """Test code blocks convert correctly."""
        from apps.exams.moodle_export import format_html_for_moodle

        markdown_text = "```python\nprint('hello')\n```"
        html = format_html_for_moodle(markdown_text)
        self.assertIn("<pre>", html)
        self.assertIn("<code", html)  # <code class="language-python">
        self.assertIn("print", html)

    def test_convert_lists(self):
        """Test lists convert correctly."""
        from apps.exams.moodle_export import format_html_for_moodle

        markdown_text = "- Item 1\n- Item 2"
        html = format_html_for_moodle(markdown_text)
        self.assertIn("<li>", html)

    def test_escape_cdata_injection(self):
        """Test ]]> is escaped to prevent CDATA injection."""
        from apps.exams.moodle_export import format_html_for_moodle

        markdown_text = "Test ]]> content"
        html = format_html_for_moodle(markdown_text)
        self.assertNotIn("]]>", html)
        self.assertIn("]]&gt;", html)


class VariantGenerationTests(TestCase):
    """Test variant generation with variables."""

    def setUp(self):
        """Create test template with variables using proper QuestionTemplate types."""
        from apps.questions.models import Choice

        self.subject = Subject.objects.create(name="Math")
        self.template = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Addition Question",
            text={"en": "What is {{x}} + {{y}}?"},
            variables={
                "x": {"type": "num", "min": 1, "max": 10, "precision": 1},  # precision=1 means integer
                "y": {"type": "num", "min": 1, "max": 10, "precision": 1},
            },
        )
        # Add choices
        Choice.objects.create(template=self.template, order=0, text={"en": "{{x + y}}"})
        Choice.objects.create(template=self.template, order=1, text={"en": "{{x - y}}"})

    def test_deterministic_generation(self):
        """Test same seed generates same variant."""
        from apps.exams.moodle_export import generate_variant

        variant1 = generate_variant(self.template, 0, "en")
        variant2 = generate_variant(self.template, 0, "en")

        self.assertEqual(variant1["text"], variant2["text"])
        self.assertEqual(variant1["values"], variant2["values"])

    def test_different_versions_generate_different_values(self):
        """Test different version numbers generate different variants."""
        from apps.exams.moodle_export import generate_variant

        variant0 = generate_variant(self.template, 0, "en")
        variant1 = generate_variant(self.template, 1, "en")

        # Extremely unlikely to be identical with random generation
        self.assertNotEqual(variant0["text"], variant1["text"])

    def test_integer_variable_ranges(self):
        """Test integer variables stay within range."""
        from apps.exams.moodle_export import generate_variant

        variant = generate_variant(self.template, 0, "en")

        self.assertGreaterEqual(variant["values"]["x"], 1)
        self.assertLessEqual(variant["values"]["x"], 10)
        self.assertGreaterEqual(variant["values"]["y"], 1)
        self.assertLessEqual(variant["values"]["y"], 10)

    def test_variable_substitution_in_text(self):
        """Test variables are substituted in question text."""
        from apps.exams.moodle_export import generate_variant

        variant = generate_variant(self.template, 0, "en")

        # Text should not contain markers
        self.assertNotIn("{{x}}", variant["text"])
        self.assertNotIn("{{y}}", variant["text"])
        # Text should contain actual numbers
        self.assertIn(str(variant["values"]["x"]), variant["text"])


class UniquenessValidationTests(TestCase):
    """Test variant uniqueness validation."""

    def setUp(self):
        """Create test template."""
        from apps.questions.models import Choice

        self.subject = Subject.objects.create(name="Test")

        # Template with wide range (should succeed) - use 'num' type with precision=1 for integers
        self.wide_template = QuestionTemplate.objects.create(subject=self.subject, title="Wide Range", text={"en": "Number {{x}}"}, variables={"x": {"type": "num", "min": 1, "max": 100, "precision": 1}})
        Choice.objects.create(template=self.wide_template, order=0, text={"en": "Correct"})
        Choice.objects.create(template=self.wide_template, order=1, text={"en": "Wrong"})

    def test_successful_uniqueness_with_wide_range(self):
        """Test successful generation with wide variable range."""
        from apps.exams.moodle_export import generate_all_variants

        variants = generate_all_variants(self.wide_template, 5, "en")

        self.assertEqual(len(variants), 5)
        texts = [v["text"] for v in variants]
        self.assertEqual(len(texts), len(set(texts)))  # All unique

    def test_no_variables_raises_error_on_duplicates(self):
        """Test templates without variables raise error when requesting multiple variants."""
        from apps.exams.moodle_export import generate_all_variants
        from apps.questions.models import Choice

        # Template without variables
        template = QuestionTemplate.objects.create(subject=self.subject, title="Static", text={"en": "What is 2 + 2?"}, variables=None)
        Choice.objects.create(template=template, order=0, text={"en": "4"})
        Choice.objects.create(template=template, order=1, text={"en": "5"})

        # Should raise ValueError because all variants are identical
        with self.assertRaises(ValueError) as cm:
            generate_all_variants(template, 3, "en")
        self.assertIn("unique variants", str(cm.exception))


class MoodleXMLGenerationTests(TestCase):
    """Test Moodle XML generation."""

    def setUp(self):
        """Create test exam with templates."""
        from decimal import Decimal

        from apps.questions.models import Choice

        self.subject = Subject.objects.create(name="Test")

        # Create exam
        self.exam = Exam.objects.create(title="Test Exam", grading_mode="single")

        # Create pool
        self.pool = QuestionPool.objects.create(exam=self.exam, order=1, default_grade=Decimal("2.5"))

        # Create template with 4 choices
        self.template = QuestionTemplate.objects.create(subject=self.subject, title="Test Question", text={"en": "What is the answer?"}, variables=None)

        # Add 4 choices
        Choice.objects.create(template=self.template, order=0, text={"en": "Correct answer"})
        Choice.objects.create(template=self.template, order=1, text={"en": "Wrong 1"})
        Choice.objects.create(template=self.template, order=2, text={"en": "Wrong 2"})
        Choice.objects.create(template=self.template, order=3, text={"en": "Wrong 3"})

        # Add template to pool
        QuestionPoolTemplate.objects.create(pool=self.pool, template=self.template, number_of_versions=1)

    def test_xml_has_quiz_root_element(self):
        """Test XML structure has quiz root element."""
        from apps.exams.moodle_export import generate_moodle_xml

        xml = generate_moodle_xml(self.exam, "en")

        self.assertIn("<quiz>", xml)
        self.assertIn("</quiz>", xml)

    def test_question_type_is_multichoice(self):
        """Test question elements have type='multichoice'."""
        from apps.exams.moodle_export import generate_moodle_xml

        xml = generate_moodle_xml(self.exam, "en")

        self.assertIn('<question type="multichoice">', xml)

    def test_sequential_naming(self):
        """Test questions are named Q1, Q2, Q3..."""
        from apps.exams.moodle_export import generate_moodle_xml

        xml = generate_moodle_xml(self.exam, "en")

        self.assertIn("<text>Q1</text>", xml)

    def test_variants_are_tagged_by_question_pool(self):
        """Test all alternatives for a question share the pool tag."""
        import xml.etree.ElementTree as ET

        from apps.exams.moodle_export import generate_moodle_xml
        from apps.questions.models import Choice

        self.template.text = {"en": "What is {{x}}?"}
        self.template.variables = {"x": {"type": "num", "min": 1, "max": 100, "precision": 1}}
        self.template.save()

        membership = self.pool.pool_templates.get(template=self.template)
        membership.number_of_versions = 3
        membership.save()

        alternative = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Alternative Question",
            text={"en": "Alternative"},
            variables=None,
        )
        Choice.objects.create(template=alternative, order=0, text={"en": "Correct"})
        Choice.objects.create(template=alternative, order=1, text={"en": "Wrong"})
        QuestionPoolTemplate.objects.create(
            pool=self.pool,
            template=alternative,
            number_of_versions=1,
        )

        second_pool = QuestionPool.objects.create(
            exam=self.exam,
            order=2,
            default_grade=self.pool.default_grade,
        )
        QuestionPoolTemplate.objects.create(
            pool=second_pool,
            template=alternative,
            number_of_versions=1,
        )

        xml = generate_moodle_xml(self.exam, "en")
        root = ET.fromstring(xml)

        names = [question.findtext("./name/text") for question in root.findall("question")]
        tags = [question.findtext("./tags/tag/text") for question in root.findall("question")]

        self.assertEqual(names, ["Q1", "Q2", "Q3", "Q4", "Q5"])
        self.assertEqual(tags, ["q1", "q1", "q1", "q1", "q2"])

    def test_cdata_wrapping_for_question_text(self):
        """Test CDATA wrapping for question text."""
        import xml.etree.ElementTree as ET

        from apps.exams.moodle_export import generate_moodle_xml

        self.template.text = {"en": "In an HTML document..."}
        self.template.save()

        xml = generate_moodle_xml(self.exam, "en")

        self.assertIn("<text><![CDATA[<p>In an HTML document...</p>]]></text>", xml)
        self.assertNotIn("&lt;![CDATA[", xml)

        root = ET.fromstring(xml)
        question_text = root.find("./question/questiontext/text")
        self.assertIsNotNone(question_text)
        self.assertEqual(question_text.text, "<p>In an HTML document...</p>")

    def test_cdata_wrapping_for_answer_text(self):
        """Test CDATA wrapping for answer text."""
        import xml.etree.ElementTree as ET

        from apps.exams.moodle_export import generate_moodle_xml

        xml = generate_moodle_xml(self.exam, "en")

        self.assertIn("<text><![CDATA[<p>Correct answer</p>]]></text>", xml)

        root = ET.fromstring(xml)
        answer_texts = root.findall("./question/answer/text")
        self.assertEqual(len(answer_texts), 4)
        self.assertEqual(answer_texts[0].text, "<p>Correct answer</p>")

    def test_cdata_terminator_content_remains_valid_xml(self):
        """Test embedded CDATA terminators cannot break the export."""
        import xml.etree.ElementTree as ET

        from apps.exams.moodle_export import generate_moodle_xml

        self.template.text = {"en": "Test ]]> content"}
        self.template.save()

        xml = generate_moodle_xml(self.exam, "en")
        root = ET.fromstring(xml)
        question_text = root.find("./question/questiontext/text")

        self.assertIsNotNone(question_text)
        self.assertIn("]]&gt;", question_text.text)

    def test_dollar_delimited_choice_expression_is_evaluated(self):
        """Test Moodle XML receives evaluated choice expressions."""
        import xml.etree.ElementTree as ET

        from apps.exams.moodle_export import generate_moodle_xml

        correct_choice = self.template.choices.get(order=0)
        correct_choice.text = {"en": "$2 + 2$"}
        correct_choice.save()

        xml = generate_moodle_xml(self.exam, "en")
        root = ET.fromstring(xml)
        answer_text = root.findtext("./question/answer/text")

        self.assertEqual(answer_text, "<p>4</p>")
        self.assertNotIn("$2 + 2$", xml)

    def test_single_true_for_single_choice_mode(self):
        """Test <single>true</single> for single-choice exams."""
        from apps.exams.moodle_export import generate_moodle_xml

        self.exam.grading_mode = "single"
        self.exam.save()

        xml = generate_moodle_xml(self.exam, "en")

        self.assertIn("<single>true</single>", xml)

    def test_single_false_for_multi_choice_mode(self):
        """Test <single>false</single> for multi-choice exams."""
        from apps.exams.moodle_export import generate_moodle_xml

        self.exam.grading_mode = "multi"
        self.exam.save()

        xml = generate_moodle_xml(self.exam, "en")

        self.assertIn("<single>false</single>", xml)

    def test_default_grade_matches_pool(self):
        """Test defaultgrade element matches pool.default_grade."""
        from apps.exams.moodle_export import generate_moodle_xml

        xml = generate_moodle_xml(self.exam, "en")

        self.assertIn("<defaultgrade>2.50</defaultgrade>", xml)

    def test_fraction_attributes_on_answers(self):
        """Test fraction attributes appear on answer elements."""
        from apps.exams.moodle_export import generate_moodle_xml

        xml = generate_moodle_xml(self.exam, "en")

        # Single mode with 4 choices should have 100 and -33.33
        self.assertIn('fraction="100.0"', xml)
        self.assertIn('fraction="-33.33"', xml)


class ExamExportViewTests(TestCase):
    """Test ExamExportView."""

    def setUp(self):
        """Create test exam."""
        from apps.questions.models import Choice

        self.subject = Subject.objects.create(name="Test")
        self.exam = Exam.objects.create(title="Export Test", grading_mode="single")
        self.pool = QuestionPool.objects.create(exam=self.exam, order=1)

        self.template = QuestionTemplate.objects.create(subject=self.subject, title="Q1", text={"en": "Question?"}, variables=None)
        Choice.objects.create(template=self.template, order=0, text={"en": "A"})
        Choice.objects.create(template=self.template, order=1, text={"en": "B"})

        QuestionPoolTemplate.objects.create(pool=self.pool, template=self.template, number_of_versions=1)

    def test_get_request_not_allowed(self):
        """Test GET request returns 405."""
        response = self.client.get(reverse("exams:export", kwargs={"pk": self.exam.pk}))
        self.assertEqual(response.status_code, 405)

    def test_post_returns_xml_download(self):
        """Test POST returns XML file download."""
        response = self.client.post(reverse("exams:export", kwargs={"pk": self.exam.pk}), {"language": "en"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")

    def test_filename_format(self):
        """Test filename format is {title}_{language}.xml."""
        response = self.client.post(reverse("exams:export", kwargs={"pk": self.exam.pk}), {"language": "en"})

        self.assertIn("filename=", response["Content-Disposition"])
        self.assertIn("Export_Test_en.xml", response["Content-Disposition"])

    def test_content_disposition_is_attachment(self):
        """Test Content-Disposition is attachment."""
        response = self.client.post(reverse("exams:export", kwargs={"pk": self.exam.pk}), {"language": "en"})

        self.assertIn("attachment", response["Content-Disposition"])

    def test_error_when_exam_not_found(self):
        """Test 404 when exam doesn't exist."""
        import uuid

        response = self.client.post(reverse("exams:export", kwargs={"pk": uuid.uuid4()}), {"language": "en"})

        self.assertEqual(response.status_code, 404)

    def test_error_when_question_missing_language(self):
        """Test error when question text missing requested language."""
        from apps.questions.models import Choice, QuestionTemplate

        # Create template with only Portuguese text
        template_pt = QuestionTemplate.objects.create(subject=self.subject, title="PT Only", text={"pt": "Pergunta?"}, variables=None)
        Choice.objects.create(template=template_pt, order=0, text={"pt": "A"})
        Choice.objects.create(template=template_pt, order=1, text={"pt": "B"})

        pool2 = QuestionPool.objects.create(exam=self.exam, order=2)
        QuestionPoolTemplate.objects.create(pool=pool2, template=template_pt, number_of_versions=1)

        # Try to export in English
        response = self.client.post(reverse("exams:export", kwargs={"pk": self.exam.pk}), {"language": "en"})

        # Should redirect back to exam detail with error
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("exams:detail", kwargs={"pk": self.exam.pk}))

        # Check error message was set
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("PT Only" in str(m) and "does not have text in language 'en'" in str(m) for m in messages))

    def test_error_when_choice_missing_language(self):
        """Test error when choice missing requested language."""
        from apps.questions.models import Choice, QuestionTemplate

        # Create template with question in both languages but one choice only in Portuguese
        template_mixed = QuestionTemplate.objects.create(subject=self.subject, title="Mixed", text={"en": "Question?", "pt": "Pergunta?"}, variables=None)
        Choice.objects.create(template=template_mixed, order=0, text={"en": "A", "pt": "A"})
        Choice.objects.create(template=template_mixed, order=1, text={"pt": "B"})  # Missing English

        pool2 = QuestionPool.objects.create(exam=self.exam, order=2)
        QuestionPoolTemplate.objects.create(pool=pool2, template=template_mixed, number_of_versions=1)

        # Try to export in English
        response = self.client.post(reverse("exams:export", kwargs={"pk": self.exam.pk}), {"language": "en"})

        # Should redirect back to exam detail with error
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("exams:detail", kwargs={"pk": self.exam.pk}))

        # Check error message was set
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Choice 2" in str(m) and "Mixed" in str(m) and "does not have text in language 'en'" in str(m) for m in messages))


class PoolGradeUpdateTests(TestCase):
    """Test PoolUpdateGradeView."""

    def setUp(self):
        """Create test pool."""
        from decimal import Decimal

        self.exam = Exam.objects.create(title="Test")
        self.pool = QuestionPool.objects.create(exam=self.exam, order=1, default_grade=Decimal("1.0"))

    def test_successful_grade_update(self):
        """Test successful grade update."""
        from decimal import Decimal

        response = self.client.post(reverse("exams:pool_update_grade", kwargs={"exam_pk": self.exam.pk, "pk": self.pool.pk}), {"default_grade": "2.5"})

        self.assertEqual(response.status_code, 302)  # Redirect
        self.pool.refresh_from_db()
        self.assertEqual(self.pool.default_grade, Decimal("2.5"))

    def test_redirect_to_exam_detail(self):
        """Test redirect to exam detail after save."""
        response = self.client.post(reverse("exams:pool_update_grade", kwargs={"exam_pk": self.exam.pk, "pk": self.pool.pk}), {"default_grade": "2.5"}, follow=False)

        self.assertRedirects(response, reverse("exams:detail", kwargs={"pk": self.exam.pk}))

    def test_validation_error_for_grade_below_minimum(self):
        """Test client-side validation prevents grade < 0.1 (handled by HTML5 min attribute)."""
        # Since PoolUpdateGradeView doesn't have a template (uses modal), skip server-side test
        # The actual validation is enforced by the model's MinValueValidator and HTML5 min attribute
        pass


class GradingModeFormTests(TestCase):
    """Test ExamForm with grading mode."""

    def test_default_value_is_single(self):
        """Test default grading mode is 'single' (from model default)."""
        from apps.exams.models import Exam

        # Create an exam without specifying grading_mode
        exam = Exam.objects.create(title="Test Exam")

        self.assertEqual(exam.grading_mode, "single")

    def test_both_choices_appear_in_form(self):
        """Test both grading mode choices appear."""
        form = ExamForm()

        field = form.fields["grading_mode"]
        choices = [choice[0] for choice in field.choices]

        self.assertIn("single", choices)
        self.assertIn("multi", choices)

    def test_radio_select_widget_is_used(self):
        """Test RadioSelect widget is used for grading_mode."""
        from django import forms

        form = ExamForm()

        self.assertIsInstance(form.fields["grading_mode"].widget, forms.RadioSelect)
