.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _management-interface-theming:

Customize web interface themes
==============================

Nubus for UCS provides built-in light and dark themes for all web interfaces.
You can switch themes globally for all users or customize the appearance by creating your own themes.
Both options require only a configuration change with no service restart.

.. _management-interface-theming-light-dark:

Switch light and dark theme
---------------------------

All web interfaces in Nubus for UCS have a dark and a light theme.
The CSS files for the themes are at :file:`/usr/share/univention-web/themes/`.
By default, Nubus for UCS provides a ``light`` and a ``dark`` theme.

You can switch between the themes globally for all users
by changing the UCR variable :envvar:`ucs/web/theme`.
The variable's value corresponds to the CSS filename without its extension.
For example, the value ``light`` uses the :file:`light.css` theme for all UCS web interfaces.

To apply the theme switch, reload the web interface in the browser.

.. _management-interface-theming-custom:

Create a custom theme
---------------------

Nubus for UCS allows providing custom themes for the web interfaces.

.. important::

   Don't edit the files
   :file:`/usr/share/univention-web/themes/dark.css` and
   :file:`/usr/share/univention-web/themes/light.css`,
   because upgrades to Nubus for UCS can overwrite your changes.

To create a custom theme, use the following steps:

#. Copy one of the CSS files to a separate file.

   For example:
   :file:`/usr/share/univention-web/themes/mytheme.css`

   The files
   :file:`/usr/share/univention-web/themes/dark.css`
   and :file:`/usr/share/univention-web/themes/light.css`
   contain the same list of `CSS variables <https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascading_variables/Using_custom_properties>`_.
   Other CSS files use these variables.

   These CSS variables are the supported configuration set for UCS web interfaces.
   The names and use cases for these variables remain stable across Nubus for UCS updates,
   but Univention may add new names and use cases.

#. Change the value of the :envvar:`ucs/web/theme` UCR variable
   to the name of your custom theme.

   For example, set the value to ``mytheme``.

#. Reload the web interface in your browser.
   The UCR variable change takes effect without requiring a service restart.

Some UCS web interfaces import their own :file:`custom.css` file
which you can use to adjust their design.
The files start empty after you install Nubus for UCS,
and updates don't change these files,
so your customizations persist.

* For *Management UI*: :file:`/usr/share/univention-management-console-login/css/custom.css`

* For the Portal:
  :file:`/usr/share/univention-portal/css/custom.css`

.. important::

   A given `CSS selector <https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics/Basic_selectors>`_
   may break when you install a Nubus for UCS update.

