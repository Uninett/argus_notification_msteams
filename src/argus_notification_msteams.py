"Allow argus-server to send notifications to MS Teams"

import enum
import json
import logging

import pymsteams

from django.conf import settings
from django import forms
# from django.template.loader import render_to_string

from argus.notificationprofile.media.base import NotificationMedium


LOG = logging.getLogger(__name__)

__version__ = "0.1"
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
    incident_dict = modelinstance_to_dict(event.incident)
    for field in ("id", "source_id"):
        incident_dict.pop(field)

    context = {
        "title": title,
        "event": event,
        "incident_dict": incident_dict,
    }
    subject = f"{settings.NOTIFICATION_SUBJECT_PREFIX}{title}"
    return subject, context, event.incident.level


def _build_card(teams_webhook, subject, context, level):
    card = pymsteams.connectorcard(teams_webhook)
    card.title(subject)
    card.color(SEVERITY_COLOR_MAPPING[level])
    fact_section = pymsteams.cardsection()
    fact_section.addFact("Status", context['event'].type)
    fact_section.addFact("Actor", context['event'].actor.username)
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

    class Form(forms.Form):
        webhook = forms.URLField(required=True)

    @classmethod
    def validate(cls, instance, dict_):
        form = cls.Form(dict_["settings"])
        if not form.is_valid():
            raise ValidationError(form.errors)
        return form.cleaned_data

    @classmethod
    def get_label(self, destination):
        return f"MS TEAMS #{destination.pk}"

    @staticmethod
    def send(event, destinations, **_):
        teams_destinations = destinations.filter(media__slug=MSTeamsNotification.MEDIA_SLUG)
        if not teams_destinations:
            return False

        subject, message, level = _build_context(event)

        for destination in teams_destinations:
            webhook = destination.settings["webhook"]
            card = _build_card(teams_webhook, subject, message, event.level)

            try:
                card.send()
            except pymsteams.TeamsWebhookException as e:
                label = destination.label or MSTeamsNotification.get_label(destination)
                LOG.exception("Could not send to MS Teams {label}: {e}")
