**UPGRADING**
==============
**1.0.0**

For version 1, we replaced the dependency ``pymsteams`` with ``apprise``.

This is because how things are shared with MS Teams have changed completely,
which also means that a new MS Teams workflow needs to be created in place of
any existing webhooks. See the **README** for instructions.

After upgrading, the ``pymsteams`` library may be cleaned away using ``pip
uninstall pymsteams`` or something similar.

**1.1.0**

The settings key used to store the webhook URL on a destination has also
changed, from ``webhook`` to ``destination_url``, to match the other Apprise
based media plugins. Existing destinations that still have their URL stored
under ``webhook`` keep working.
Still, it is recommended to re-create your destinations using the updated ``destination_url`` term.
