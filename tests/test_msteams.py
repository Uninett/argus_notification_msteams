#from django.conf import settings
#from django.test import TestCase, SimpleTestCase

#from argus.incident.factories import IncidentFactory
#from argus_notification_msteams import _build_context, MSTeamsNotification


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
