**UPGRADING**
==============
**1.0.0**

For version 1, we replaced the dependency ``pymsteams`` with ``apprise``.

This is because how things are shared with MS Teams have changed completely,
which also means that a new MS Teams workflow needs to be created in place of
any existing webhooks. See the **README** for instructions.

After upgrading, the ``pymsteams`` library may be cleaned away using ``pip
uninstall pymsteams`` or something similar.

