from django.conf import settings
from django.test import TestCase

from argus.incident.factories import IncidentFactory
from argus_notification_msteams import _build_card, _build_context, MSTeamsNotification


class TestHelperFunctions(TestCase):

    @classmethod
    def setUpTestData(cls):
        incident = IncidentFactory()
        cls.event = incident.events.first()

    def test__build_context_subject_starts_with_fixed_prefix(self):
        subject, _, _ = _build_context(self.event)
        prefix = settings.NOTIFICATION_SUBJECT_PREFIX
        self.assertTrue(
            subject.startswith(prefix),
            f"Subject is not prefixed with {prefix}",
        )

    def test__build_context_context_has_correct_contents(self):
        _, context, _ = _build_context(self.event)
        self.assertEqual(context["title"], str(self.event))
        self.assertEqual(context["event"], self.event)

    def test__build_context_level_is_incident_level(self):
        _, _, level = _build_context(self.event)
        self.assertEqual(level, self.event.incident.level)

    def test___build_card(self):
        subject, context, level = _build_context(self.event)
        webhook = "https://example.org/"
        card = _build_card(webhook, subject, context, level)
        self.assertEqual(card.hookurl, webhook)
        self.assertEqual(card.payload["title"], subject)
        # One section
        self.assertEqual(len(card.payload["sections"]), 1)
        # Only containing facts
        self.assertIn("facts", card.payload["sections"][0].keys())
