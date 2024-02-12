.. SPDX-FileCopyrightText: 2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _banner:

Consent for using Cookies
=========================

Both the UCS Portal and the Univention Management Console (UMC)
use cookies and store them on the user's computer.
Depending on your use case and the public presence of your UCS Portal,
you may have to inform the user about the use of cookies.

When enabled, both the UCS Portal and the UMC
show a cookie consent banner that the user must accept to continue.
You can configure the content using |UCSUCRVs|.

.. _banner-usage:

Usage of the cookie consent banner
----------------------------------

To enable and customize the content of the cookie consent banner, use the
following steps:

#. To enable the cookie consent banner, set the UCR variable
   :envvar:`umc/cookie-banner/show`
   to ``true``.
   The banner then shows the default content.

#. To customize the title and the text,
   set the UCR variables
   :envvar:`umc/cookie-banner/title`
   and
   :envvar:`umc/cookie-banner/text`
   to your liking.

   Note that both settings allow a language-specific configuration.
   For more information, see the section :ref:`banner-reference`.

#. You can also optionally set the following variables:

   * The name of the cookie as UCS stores it on the user's system with
     :envvar:`umc/cookie-banner/cookie`.

   * The domains for which UCS shows the cookie consent banner with
     :envvar:`umc/cookie-banner/domains`.

Setting the appropriate UCR variables is sufficient to enable and customize the
cookie consent banner.

To restore the default texts, unset the
:envvar:`umc/cookie-banner/title`
and
:envvar:`umc/cookie-banner/text`
UCR variables.
To turn off the cookie banner completely,
set :envvar:`umc/cookie-banner/show` to ``false``.

.. _banner-reference:

UCR reference for cookie consent banner
---------------------------------------

Use the following UCR variables to configure the cookie banner dialog.

.. envvar:: umc/cookie-banner/cookie

   The variable sets the name of the cookie.
   In the default setting, the value is empty.
   UCS then uses the name ``univentionCookieSettingsAccepted`` for the cookie.

.. envvar:: umc/cookie-banner/domains

   Optional setting for the domains for which the cookie consent banner dialog is active.
   The value is a comma-separated list of domain names,
   for which UCS shows the cookie consent banner.
   For an empty list, UCS shows the banner for all domain names.
   The domain matches from the end of the string.

   Examples:

   * The value ``example.com`` matches ``portal.example.com`` and ``sso.example com``.
     UCS shows the banner for both domain names.

   * For the value ``portal.example.com`` UCS doesn't show the cookie consent
     banner for ``sso.example.com``, but for ``portal.example.com``.

.. envvar:: umc/cookie-banner/show

   The variable controls, if the browser shows the cookie consent banner.
   The default value is ``false``.
   To show the cookie consent banner, set the variable to ``true``.

.. envvar:: umc/cookie-banner/title

   Sets the title for the consent banner dialog.
   In the default setting,
   the value is empty and UCS provides a default title for English and German.
   Use :samp:`umc/cookie-banner/title/{LANGUAGE}` with a two letter language code from
   `ISO 639-1 <w-iso-639-1_>`_
   for :samp:`{LANGUAGE}` to set titles for different languages.

.. envvar:: umc/cookie-banner/text

   Sets the text for the cookie consent banner dialog.
   In the default setting,
   the value is empty and UCS provides a default text for English and German.
   Use :samp:`umc/cookie-banner/text/{LANGUAGE}` with a two letter language code from
   `ISO 639-1 <w-iso-639-1_>`_
   for :samp:`{LANGUAGE}` to set text content for different languages.
