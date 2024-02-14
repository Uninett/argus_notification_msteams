"Allow argus-server to send notifications to MS Teams"

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pymsteams

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

__version__ = "0.6.0"
__all__ = [
    "MSTeamsNotification",
]


SEVERITY_COLOR_MAPPING = {
    1: "#910041",  # Purpleish
    2: "#dc0000",  # Red
    3: "#fd8c00",  # Orange
    4: "#fdc500",  # Yellow
    5: "#4CAF50",  # Green
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


def _build_card(teams_webhook, context):
    card = pymsteams.connectorcard(teams_webhook)
    card.title(context["subject"])
    card.color(SEVERITY_COLOR_MAPPING[context["level"]])
    card.text(context['message'])
    fact_section = pymsteams.cardsection()
    fact_section.addFact("Status", context['status'])
    fact_section.addFact("Actor", context['actor'])
    if context["expiration"]:
        fact_section.addFact("Expires", context['expiration'])
    for field, value in context["incident_dict"].items():
        fact_section.addFact(field, value)
    card.addSection(fact_section)
    return card


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

        for destination in teams_destinations:
            label = destination.label or cls.get_label(destination)
            webhook = destination.settings[cls.MEDIA_SETTINGS_KEY]
            card = _build_card(webhook, context)

            try:
                result = card.send()
            except pymsteams.TeamsWebhookException as e:
                LOG.exception("Could not send to MS Teams %s: %s", label, e)
            else:
                if result is not True:
                    LOG.exception("Could not send to MS Teams %s: Unknown reason", label)

        return True
