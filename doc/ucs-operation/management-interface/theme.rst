.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _management-interface-theming:

Theming
=======

.. _central-theming:

Switching between dark and light theme for |UCSWEB|\ s
------------------------------------------------------

All |UCSWEB|\ s have a dark and a light theme that can be switched between with
the |UCSUCRV| :envvar:`ucs/web/theme`. The value of :envvar:`ucs/web/theme`
corresponds to a CSS file under :file:`/usr/share/univention-web/themes/` with
the same name (without file extension). For example, setting
:envvar:`ucs/web/theme` to ``light`` will use
:file:`/usr/share/univention-web/themes/light.css` as theme for all |UCSWEB|\ s.

.. _central-theming-custom:

Creating a custom theme/Adjusting the design of |UCSWEB|\ s
-----------------------------------------------------------

To customize a theme for |UCSWEB|\ s don't edit the files
:file:`/usr/share/univention-web/themes/dark.css` and
:file:`/usr/share/univention-web/themes/light.css`,
because UCS upgrades can overwrite your changes.
Instead, copy one of these files to, for example,
:file:`/usr/share/univention-web/themes/mytheme.css`
and set the |UCSUCRV| :envvar:`ucs/web/theme` to ``mytheme``.

The files
:file:`/usr/share/univention-web/themes/dark.css`
and
:file:`/usr/share/univention-web/themes/light.css`
contain the same list of `CSS variables <mozilla-css-custom-properties_>`_.
Other CSS files use these CSS variables.
These CSS variables are the supported layer of configurability for |UCSWEB|\ s.
The names and use cases for these variables don't change between UCS upgrades,
but Univention may add additional names and use cases.

Some |UCSWEB|\ s import their own local :file:`custom.css` file
which you can use to adjust the design of the following pages:

* For :ref:`central-user-interface`: :file:`/usr/share/univention-management-console-login/css/custom.css`

* For :ref:`central-portal`: :file:`/usr/share/univention-portal/css/custom.css`

The files are empty during the installation of UCS.
UCS updates don't change these files.

.. important::

   Be aware, however, that a given `CSS selector <mozilla-css-selectors_>`_
   may break when installing a UCS update.

