"Allow argus-server to send notifications to MS Teams"

import enum
import json
import logging

import pymsteams

from django.conf import settings
from django import forms

from argus.notificationprofile.media.base import NotificationMedium


LOG = logging.getLogger(__name__)

__version__ = "0.3"
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

    class Form(forms.Form):
        webhook = forms.URLField(required=True)

    @classmethod
    def validate(cls, instance, dict_, _):
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

        subject, context = _build_context(event)

        for destination in teams_destinations:
            label = destination.label or MSTeamsNotification.get_label(destination)
            webhook = destination.settings["webhook"]
            card = _build_card(teams_webhook, subject, context)

            try:
                result = card.send()
            except pymsteams.TeamsWebhookException as e:
                LOG.exception("Could not send to MS Teams {label}: {e}")
            else:
                if result is not True:
                    LOG.exception("Could not send to MS Teams {label}: Unknown reason")
