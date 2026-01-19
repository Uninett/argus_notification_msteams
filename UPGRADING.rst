**UPGRADING**
==============
**1.0.0**

For version 1, we replaced the dependency ``pymsteams`` with ``appraise``.

When upgrading, ``pymsteams`` might need to be removed using ``pip-recipe`` or something similar.

This also means that a new MS Teams workflow needs to be created in place of any existing webhooks.
See the **README** for instructions.

