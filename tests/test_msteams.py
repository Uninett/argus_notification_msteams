from django.conf import settings
from django.test import TestCase, SimpleTestCase

from argus.incident.factories import IncidentFactory
from argus_notification_msteams import _build_card, _build_context, MSTeamsNotification


# class TestHelperFunctions(TestCase):
# 
#     @classmethod
#     def setUpTestData(cls):
#         incident = IncidentFactory()
#         cls.event = incident.events.first()
# 
#     def test__build_context_subject_starts_with_fixed_prefix(self):
#         context = _build_context(self.event)
#         prefix = settings.NOTIFICATION_SUBJECT_PREFIX
#         self.assertTrue(
#             context["subject"].startswith(prefix),
#             f"Subject is not prefixed with {prefix}",
#         )
# 
#     def test__build_context_context_has_correct_contents(self):
#         context = _build_context(self.event)
#         incident = self.event.incident
#         expected_context_keys = set((
#             "subject",
#             "title",
#             "status",
#             "expiration",
#             "level",
#             "actor",
#             "message",
#             "incident_dict",
#         ))
#         self.assertEqual(set(context.keys()), expected_context_keys)
# 
#     def test__build_context_level_is_incident_level(self):
#         context = _build_context(self.event)
#         self.assertEqual(context["level"], self.event.incident.level)


class TestCardBuilder(SimpleTestCase):

    def test___build_card(self):
        context = {
            "subject": "test",
            "title": "title",
            "status": "STA",
            "expiration": "2022-11-178T11:46+01:00",
            "level": 3,
            "actor": "tester@eaxmple.com",
            "message": "this is a test notification!",
            "incident_dict": {
                "key1": "value1",
            },
        }
        webhook = "https://example.org/"
        card = _build_card(webhook, context)
        self.assertEqual(card.hookurl, webhook)
        self.assertEqual(card.payload["title"], context["subject"])
        # One section
        self.assertEqual(len(card.payload["sections"]), 1)
        # Only containing facts
        self.assertIn("facts", card.payload["sections"][0].keys())
