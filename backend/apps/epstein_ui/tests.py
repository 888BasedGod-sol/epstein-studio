import json
from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from . import views


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "epstein-ui-tests",
        }
    }
)
class SecurityHardeningTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="alice", password="p@ssword123")

    def test_is_public_outbound_url_allows_known_public_host(self):
        with mock.patch("apps.epstein_ui.views.socket.getaddrinfo") as mocked_addr:
            mocked_addr.return_value = [(None, None, None, None, ("140.82.114.6", 0))]
            allowed = views._is_public_outbound_url(
                "https://api.github.com/repos/org/repo/issues",
                views.ALLOWED_OUTBOUND_HOSTS,
            )
        self.assertTrue(allowed)

    def test_is_public_outbound_url_rejects_private_ip_resolution(self):
        with mock.patch("apps.epstein_ui.views.socket.getaddrinfo") as mocked_addr:
            mocked_addr.return_value = [(None, None, None, None, ("127.0.0.1", 0))]
            allowed = views._is_public_outbound_url(
                "https://api.github.com/repos/org/repo/issues",
                views.ALLOWED_OUTBOUND_HOSTS,
            )
        self.assertFalse(allowed)

    def test_report_content_is_rate_limited(self):
        self.client.login(username="alice", password="p@ssword123")
        payload = {"type": "annotation", "id": "123", "reason": "spam"}

        for _ in range(views.REPORT_RATE_LIMIT_MAX):
            response = self.client.post(
                reverse("report_content"),
                data=json.dumps(payload),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200)

        blocked = self.client.post(
            reverse("report_content"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(blocked.status_code, 429)

    def test_feature_request_is_rate_limited(self):
        payload = {"title": "Feature", "description": "Please add X"}

        for _ in range(views.FEATURE_RATE_LIMIT_MAX):
            response = self.client.post(
                reverse("feature_request"),
                data=json.dumps(payload),
                content_type="application/json",
            )
            # Not configured because token is missing, but request itself is accepted.
            self.assertEqual(response.status_code, 503)

        blocked = self.client.post(
            reverse("feature_request"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(blocked.status_code, 429)
