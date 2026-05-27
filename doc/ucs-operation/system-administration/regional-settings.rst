.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-regional-settings:

Regional settings
=================

This page describes system settings that affect language, keyboard layout,
time zone, and time synchronization on a system running
Nubus for UCS.

.. _system-administration-language-locale-keyboard-settings:

Language, locale, and keyboard settings
---------------------------------------

On Linux, *locales* define localization properties for software.
Locales include settings for date formats, currency formats,
character sets, and the language for internationalized programs.
To change the installed locales:

#. To open the :guilabel:`Language settings` management module,
   in the *Univention Portal* go to :menuselection:`System --> Language settings --> Language settings`.
   :numref:`system-administration-language-settings-figure`
   shows the management module.

#. Set the default locale in :guilabel:`Default system locale`.

.. _system-administration-language-settings-figure:

.. figure:: /images/computers_timezone.*
   :alt: The Language settings management module shows locale, keyboard layout, and time zone settings.

   Configuring the language settings

.. _system-administration-time-zone-synchronization:

Time zone and time synchronization
----------------------------------

To change the system time zone:

#. To open the :guilabel:`Language settings` management module,
   in the *Univention Portal* go to :menuselection:`System --> Language settings`.

#. Go to :menuselection:`Time zone and keyboard settings --> Time zone`.

Inconsistent system time between hosts in a domain
can cause many errors.
For example, it can affect the following components:

* Log file reliability.

* Kerberos operation.

* Evaluation of password validity periods.

The :term:`Primary Directory Node` usually acts as the timeserver for a domain.
To include external NTP servers as time sources,
set the :term:`UCR variables <UCR variable>` :envvar:`timeserver`,
:envvar:`timeserver2`, and :envvar:`timeserver3`.

To synchronize the time manually,
run :command:`ntpdate`.

Windows clients in a Samba domain
accept only signed NTP time requests.
If you set the :term:`UCR variable` :envvar:`ntp/signed` to ``yes``,
Samba signs NTP replies.
