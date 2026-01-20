argus_notification_msteams
==========================

This is a plugin to send notifications to MSTeams from
`Argus <https://github.com/Uninett/argus-server>`_

Different levels of incidents have hard-coded icon colors, based on those used in the Argus frontend.

Version 0.5.1 and older can be used by argus-server version 1.9.x to 1.13.x.

Django settings
---------------

Add ``argus_notification_msteams.MSTeamsNotification`` to ``MEDIA_PLUGINS``::

    MEDIA_PLUGINS = [
        ..
        "argus_notification_msteams.MSTeamsNotification",
    ]

The plugin uses the setting ``NOTIFICATION_SUBJECT_PREFIX``.

Configuration
-------------

Create a workflow inside MS Teams to send webhook alerts to a chat or channel.
This lets you use "Copy webhook link" to get a long url that needs to be
stored in the ``settings``-field.

You can test without invoking the frontend by adding the webhook manually in
Django admin.

POST-ing to the API:

/api/v2/notificationprofiles/destinations/, POSTed body::

    {
      "media": "msteams",
      "label": "whatever",
      "settings": {
        "webhook": "https://msteams.domain/some-very-long-webhook-specific-path"
      }
    }

GET-ing from the API:

/api/v2/notificationprofiles/destinations/{id}/, received result::

  {
    "pk": 0,
    "media": {
      "slug": "msteams",
      "name": "MS Teams"
    },
    "label": "whatever",
    "suggested_label": "whatever",
    "settings": {
      "webhook": "https://msteams.domain/some-very-long-webhook-specific-path"
    }
  }
