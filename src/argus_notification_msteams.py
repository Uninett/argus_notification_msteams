"Allow argus-server to send notifications to MS Teams"

from __future__ import annotations

import logging
from typing import Iterable, TYPE_CHECKING

from apprise import NotifyType
from django.conf import settings

from argus.notificationprofile.models import DestinationConfig
from argus.notificationprofile.media.base import AppriseMedium, modelinstance_to_dict

if TYPE_CHECKING:
    from argus.incident.models import Event


LOG = logging.getLogger(__name__)

__version__ = "1.1.0"
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
        "message": incident.description,
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


LEGACY_SETTINGS_KEY = "webhook"


def _get_destination_url(destination: DestinationConfig) -> str:
    settings = destination.settings
    return settings.get("destination_url") or settings.get(LEGACY_SETTINGS_KEY)


class MSTeamsNotification(AppriseMedium):
    MEDIA_SLUG = "msteams"
    MEDIA_NAME = "MS Teams"
    MEDIA_JSON_SCHEMA = {
        "title": "MS Teams Settings",
        "description": "Settings for a DestinationConfig using MS Teams.",
        "type": "object",
        "required": ["destination_url"],
        "properties": {
            "destination_url": {
                "type": "string",
                "title": "Webhook (URL)",
                "format": "iri",
            }
        },
    }

    @classmethod
    def validate(cls, instance, msteams_dict: dict, user) -> dict:
        settings = msteams_dict.get("settings") or {}
        if LEGACY_SETTINGS_KEY in settings and "destination_url" not in settings:
            settings = {**settings, "destination_url": settings[LEGACY_SETTINGS_KEY]}
            msteams_dict = {**msteams_dict, "settings": settings}
        return super().validate(instance, msteams_dict, user)

    @staticmethod
    def get_label(destination) -> str:
        return _get_destination_url(destination)

    @classmethod
    def get_relevant_address(cls, destination):
        return _get_destination_url(destination)

    @classmethod
    def send(
        cls, event: Event, destinations: Iterable[DestinationConfig], **kwargs
    ) -> bool:
        return super().send(
            event,
            destinations,
            notify_type=NOTIFY_TYPE_MAPPING[event.incident.level],
            **kwargs,
        )

    @staticmethod
    def create_message_context(event: Event):
        context = _build_context(event)
        subject = context["subject"]
        message = _build_message(context)
        return subject, message
