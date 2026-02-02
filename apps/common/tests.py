"""Tests for common app views."""

from django.test import TestCase
from django.urls import reverse


class HomeViewTests(TestCase):
    """Test cases for the home view."""

    def test_home_page_status_code(self):
        """Test that the home page returns a 200 status code."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_home_page_uses_correct_template(self):
        """Test that the home page uses the correct template."""
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "common/home.html")
        self.assertTemplateUsed(response, "common/base.html")

    def test_home_page_contains_welcome_text(self):
        """Test that the home page contains welcome text."""
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Welcome to Qoodle")
        self.assertContains(response, "Moodle Quiz Question Generator")

