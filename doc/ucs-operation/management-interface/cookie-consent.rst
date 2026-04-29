.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _management-interface-cookie-consent:

Consent for using cookies
=========================

Both the Univention Portal and the *Management UI*
store cookies on the user's computer.
Depending on your use case and the public profile of your Univention Portal,
you may need to inform users about the cookies.

When you enable the cookie consent banner,
both the Univention Portal and the *Management UI*
show the banner that users must accept before continuing.
You can configure the banner content using :term:`UCR variables <UCR variable>`.

.. _management-interface-cookie-consent-usage:

Configure the cookie consent banner
-----------------------------------

To enable and customize the cookie consent banner,
follow these steps:

#. Set :envvar:`umc/cookie-banner/show` to ``true``
   to enable the banner.
   The banner displays the default content.

#. To customize the title and text,
   set the UCR variables
   :envvar:`umc/cookie-banner/title`
   and
   :envvar:`umc/cookie-banner/text`
   as needed.

   Both settings support language-specific configuration.
   For more information, see :ref:`management-interface-cookie-consent-reference`.

You can also set the following variables:

:envvar:`umc/cookie-banner/cookie`
  for the name of the cookie that Nubus for UCS stores on the user's system.

:envvar:`umc/cookie-banner/domains`
  for the domains for which Nubus for UCS shows the cookie consent banner.

To restore the default content,
unset the :envvar:`umc/cookie-banner/title`
and :envvar:`umc/cookie-banner/text` UCR variables.
To deactivate the cookie banner,
set :envvar:`umc/cookie-banner/show` to ``false``.

.. _management-interface-cookie-consent-reference:

UCR reference for cookie consent banner
---------------------------------------

The following UCR variables control the cookie consent banner.

.. envvar:: umc/cookie-banner/cookie

   Sets the name of the cookie that Nubus for UCS stores on the user's system
   when the user accepts the cookie consent banner.
   If you don't set this variable,
   Nubus for UCS uses the name ``univentionCookieSettingsAccepted``.

   :Default value: not set
   :Type: string

.. envvar:: umc/cookie-banner/domains

   Sets the domains for which Nubus for UCS shows the cookie consent banner.
   The value is a comma-separated list of domain names.
   Nubus for UCS matches domains from the end,
   so a single entry covers multiple subdomains.
   If you don't set this variable,
   Nubus for UCS shows the banner for all domain names.

   Example: The value ``example.com`` matches both ``portal.example.com``
   and ``sso.example.com``.
   Both sites share the cookie,
   so users only need to accept once.

   :Default value: not set
   :Type: list

.. envvar:: umc/cookie-banner/show

   Sets whether Nubus for UCS shows the cookie consent banner
   in the Univention Portal and during sign in.

   :Default value: ``false``
   :Possible values: ``true``, ``false``
   :Type: boolean

.. envvar:: umc/cookie-banner/title

   Sets the title for the cookie consent banner.
   If you don't set this variable,
   Nubus for UCS provides a default title in English, ``Cookie Settings``,
   and German, ``Cookie-Einstellungen``.

   Use :samp:`umc/cookie-banner/title/{LANGUAGE}`
   to set a title for a specific language,
   where :samp:`{LANGUAGE}` is a two-letter ISO 639-1 language code.

   :Default value: not set
   :Type: string

.. envvar:: umc/cookie-banner/text

   Sets the text for the cookie consent banner.
   If you don't set this variable,
   Nubus for UCS provides default text in English and German
   that links to the Univention privacy policy.
   Use :samp:`umc/cookie-banner/text/{LANGUAGE}`
   to set text for a specific language,
   where :samp:`{LANGUAGE}` is a two-letter ISO 639-1 language code.

   :Default value: not set
   :Type: string

.. seealso::

   `ISO 639-1 on Wikipedia <https://en.wikipedia.org/wiki/ISO_639-1>`_
      for a list of two-letter language codes.

   `Univention Privacy statement <https://www.univention.com/privacy-statement/>`_
      for the content of the privacy statement
      that the :envvar:`umc/cookie-banner/text` UCR variable uses by default.
