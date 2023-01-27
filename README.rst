argus_notification_msteams
==========================

ALPHA-VERSION!

This is a plugin to send notifications to MSTeams from
`Argus <https://github.com/Uninett/argus-server>`_

Different levels of incidents have hard-coded colors.

Django settings
---------------

Add ``argus_notification_msteams`` to ``MEDIA_PLUGINS``::

    MEDIA_PLUGINS = [
        "argus_notification_msteams",
    ]

The plugin uses the setting ``NOTIFICATION_SUBJECT_PREFIX``.

Configuration
-------------

Create a webhook inside MS Teams, which results in an url that is stored in the
``settings``-field.

You can test without invoking the frontend by adding the webhook manually in
Django admin.

POST-ing to the API:

/api/v2/notificationprofiles/destinations/::

    {
      "media": "msteams",
      "label": "whatever",
      "settings": {
        "webhook": "https://msteams.domain/some-very-long-webhook-specific-path"
      }
    }

GET-ing from the API:

/api/v2/notificationprofiles/destinations/{id}/::

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
