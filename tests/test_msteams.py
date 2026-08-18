from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from argus_notification_msteams import (
    NOTIFY_TYPE_MAPPING,
    MSTeamsNotification,
    _build_message,
)


class MSTeamsMessageBuilderTests(SimpleTestCase):
    def test_build_message(self):
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
                "key2": "value2",
            },
        }
        message = _build_message(context)
        self.assertIn("**test**", message)
        self.assertIn("this is a test notification!", message)
        self.assertIn("**Status** STA", message)
        self.assertIn("**Actor** tester@eaxmple.com", message)
        self.assertIn("**Expires** 2022-11-178T11:46+01:00", message)
        self.assertIn("**key1** value1", message)
        self.assertIn("**key2** value2", message)


class MSTeamsNotificationBehaviorTests(SimpleTestCase):
    def setUp(self):
        self.event = MagicMock()
        self.event.pk = 1
        self.event.incident.level = 1
        self.destination = MagicMock()
        self.destination.media_id = "msteams"
        self.destination.settings = {"destination_url": "https://webhook.example.com"}
        self.destination.pk = 1

    @patch("argus.notificationprofile.media.base.Apprise")
    def test_given_incident_level_notifier_should_be_called_with_corresponding_notify_type(
        self, mock_apprise
    ):
        instance = mock_apprise.return_value
        instance.notify.return_value = True

        with self.settings(SEND_NOTIFICATIONS=True):
            with patch.object(
                MSTeamsNotification,
                "create_message_context",
                return_value=("Subject", "Body"),
            ):
                MSTeamsNotification.send(self.event, [self.destination])

        _, call_kwargs = instance.notify.call_args
        self.assertEqual(
            call_kwargs["notify_type"], NOTIFY_TYPE_MAPPING[self.event.incident.level]
        )

    def test_given_legacy_webhook_setting_get_relevant_address_should_still_find_the_url(
        self,
    ):
        self.destination.settings = {"webhook": "https://webhook.example.com"}
        address = MSTeamsNotification.get_relevant_address(self.destination)
        self.assertEqual(address, "https://webhook.example.com")


class MSTeamsNotificationValidateTests(SimpleTestCase):
    def setUp(self):
        self.instance = MagicMock()
        self.user = MagicMock()
        self.user.destinations.filter.return_value.exists.return_value = False

    def test_given_legacy_webhook_key_should_rewrite_it_to_destination_url(self):
        url = (
            "https://example.logic.azure.com/workflows/abc/triggers/manual/paths/invoke"
        )
        dict_ = {"settings": {"webhook": url}}
        cleaned_data = MSTeamsNotification.validate(self.instance, dict_, self.user)
        self.assertEqual(cleaned_data, {"destination_url": url})

    def test_given_destination_url_key_validate_should_leave_it_untouched(self):
        url = (
            "https://example.logic.azure.com/workflows/abc/triggers/manual/paths/invoke"
        )
        dict_ = {"settings": {"destination_url": url}}
        cleaned_data = MSTeamsNotification.validate(self.instance, dict_, self.user)
        self.assertEqual(cleaned_data, {"destination_url": url})

    def test_given_power_platform_workflow_url_validate_should_accept_it(self):
        # Power Automate hosts vary, so we check other parts of the URL
        url = (
            "https://default-example.0d.environment.api.powerplatform.com:443"
            "/powerautomate/automations/direct/cu/23/workflows/2a5acbf4/"
            "triggers/manual/paths/invoke?api-version=1&sig=abc"
        )
        dict_ = {"settings": {"destination_url": url}}
        cleaned_data = MSTeamsNotification.validate(self.instance, dict_, self.user)
        self.assertEqual(cleaned_data, {"destination_url": url})

    def test_given_apprise_workflow_scheme_url_validate_should_accept_it(self):
        dict_ = {"settings": {"destination_url": "workflows://example.com/abc/def/"}}
        cleaned_data = MSTeamsNotification.validate(self.instance, dict_, self.user)
        self.assertEqual(
            cleaned_data, {"destination_url": "workflows://example.com/abc/def/"}
        )

    def test_given_apprise_singular_workflow_scheme_url_validate_should_accept_it(
        self,
    ):
        dict_ = {"settings": {"destination_url": "workflow://example.com/abc/def/"}}
        cleaned_data = MSTeamsNotification.validate(self.instance, dict_, self.user)
        self.assertEqual(
            cleaned_data, {"destination_url": "workflow://example.com/abc/def/"}
        )

    def test_given_current_incoming_webhook_url_validate_should_accept_it(self):
        dict_ = {
            "settings": {
                "destination_url": (
                    "https://myteam.webhook.office.com/webhookb2/"
                    "abcd@efgh/IncomingWebhook/1234/5678"
                )
            }
        }
        cleaned_data = MSTeamsNotification.validate(self.instance, dict_, self.user)
        self.assertEqual(cleaned_data, dict_["settings"])

    def test_given_legacy_incoming_webhook_url_validate_should_accept_it(self):
        dict_ = {
            "settings": {
                "destination_url": (
                    "https://outlook.office.com/webhook/abcd@efgh/"
                    "IncomingWebhook/1234/5678"
                )
            }
        }
        cleaned_data = MSTeamsNotification.validate(self.instance, dict_, self.user)
        self.assertEqual(cleaned_data, dict_["settings"])

    def test_given_apprise_msteams_scheme_url_validate_should_raise_validation_error(
        self,
    ):
        # Apprise does not support this URL form anymores
        dict_ = {"settings": {"destination_url": "msteams://team/tokenA/tokenB/tokenC"}}
        with self.assertRaises(ValidationError):
            MSTeamsNotification.validate(self.instance, dict_, self.user)

    def test_given_url_not_pointing_to_msteams_validate_should_raise_validation_error(
        self,
    ):
        dict_ = {"settings": {"destination_url": "https://webhook.example.com"}}
        with self.assertRaises(ValidationError):
            MSTeamsNotification.validate(self.instance, dict_, self.user)
