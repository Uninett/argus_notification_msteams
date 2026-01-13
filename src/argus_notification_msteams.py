"Allow argus-server to send notifications to MS Teams"

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from apprise import Apprise, NotifyType
from django.conf import settings
from django import forms
from rest_framework.exceptions import ValidationError

from argus.notificationprofile.media.base import NotificationMedium

if TYPE_CHECKING:
    import sys

    if sys.version_info[:2] < (3, 9):
        from typing import Iterable
    else:
        from collections.abc import Iterable

    from typing import List
    from django.db.models.query import QuerySet
    from argus.incident.models import Event
    from argus.notificationprofile.models import DestinationConfig
    from argus.notificationprofile.serializers import RequestDestinationConfigSerializer


LOG = logging.getLogger(__name__)

__version__ = "0.7.0"
__all__ = [
    "MSTeamsNotification",
]


# Slightly hacky way of having different colors for different levels
# Tries to match colors used in Argus

NOTIFY_TYPE_MAPPING = {
    1: NotifyType.FAILURE,  # Red
    2: NotifyType.WARNING,  # Orange
    3: NotifyType.WARNING,  # Orange
    4: NotifyType.SUCCESS,  # Green
    5: NotifyType.INFO,  # Blue
}

def modelinstance_to_dict(obj):
    dict_ = vars(obj).copy()
    dict_.pop("_state")
    return dict_


def _build_context(event):
    title = f"{event}"
    incident = event.incident
    start_time = incident.start_time.isoformat()
    source = str(incident.source)
    subject = f"{settings.NOTIFICATION_SUBJECT_PREFIX}{title}"
    expiration = None
    if event.type == "ACK":
        expiration = event.acknowledgment.expiration.isoformat()

    incident_dict = modelinstance_to_dict(incident)
    for field in ("id", "source_id", "start_time", "end_time"):
        incident_dict.pop(field)
    incident_dict["start_time"] = start_time
    incident_dict["source"] = source

    context = {
        "subject": subject,
        "title": title,
        "status": event.type,
        "expiration": expiration,
        "level": incident.level,
        "actor": event.actor.username,
        'message': incident.description,
        "incident_dict": incident_dict,
    }
    return context


def _build_message(context) -> str:
    lines = []
    lines.append(f"**{context['subject']}**")
    lines.append(context["message"])
    lines.append(f"**Status** {context['status']}")
    lines.append(f"**Actor** {context['actor']}")
    if context["expiration"]:
        lines.append(f"**Expires** {context['expiration']}")
    for field, value in context["incident_dict"].items():
        lines.append(f"**{field}** {value}")

    return "\n\n".join(lines)


class MSTeamsNotification(NotificationMedium):

    MEDIA_SLUG = "msteams"
    MEDIA_NAME = "MS Teams"
    MEDIA_JSON_SCHEMA = {
        "title": "MS Teams Settings",
        "description": "Settings for a DestinationConfig using MS Teams.",
        "type": "object",
        "required": ["webhook"],
        "properties": {"webhook": {
            "type": "string",
            "title": "Webhook (URL)",
            "format": "iri",
        }},
    }
    MEDIA_SETTINGS_KEY = "webhook"

    class Form(forms.Form):
        webhook = forms.URLField(required=True)

    @classmethod
    def has_duplicate(cls, queryset: QuerySet, settings: dict) -> bool:
        return queryset.filter(
            settings__webhook=settings[cls.MEDIA_SETTINGS_KEY]
        ).exists()

    # No querysets beyond this point!

    @classmethod
    def get_label(self, destination):
        return f"MS TEAMS #{destination.pk}"

    @classmethod
    def validate(cls, instance: RequestDestinationConfigSerializer, dict_: dict, _) -> dict:
        form = cls.Form(dict_["settings"])
        if not form.is_valid():
            raise ValidationError(form.errors)
        return form.cleaned_data

    @classmethod
    def get_relevant_addresses(cls, destinations: Iterable[DestinationConfig]) -> List[DestinationConfig]:
        """Returns a list of teams channels the message should be sent to"""
        filtered_destinations = [
            destination.settings[cls.MEDIA_SETTINGS_KEY]
            for destination in destinations
            if destination.media_id == cls.MEDIA_SLUG
        ]
        return filtered_destinations

    @classmethod
    def send(cls, event: Event, destinations: Iterable[DestinationConfig], **_) -> bool:
        teams_destinations = cls.get_relevant_addresses(destinations)
        if not teams_destinations:
            return False

        context = _build_context(event)
        message = _build_message(context)

        for destination in teams_destinations:
            label = destination.label or cls.get_label(destination)
            webhook = destination.settings[cls.MEDIA_SETTINGS_KEY]

            notifier = Apprise()
            notifier.add(webhook)

            LOG.info("Sending message to MS Teams destination '%s'", label)
            result = notifier.notify(body=message, notify_type=NOTIFY_TYPE_MAPPING[context["level"]])

            LOG.info("notifier.notify() returned %r", result)
            if result is not True:
                LOG.error("Could not send to MS Teams %s: Unknown reason", label)

        return True
