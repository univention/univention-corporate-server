.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-regional-settings:

Regional settings
=================

This page describes system settings that affect language, keyboard layout,
time zone, and time synchronization on a Nubus for UCS system.

.. _system-administration-language-locale-keyboard-settings:

Language, locale, and keyboard settings
---------------------------------------

In Linux, localization properties for software are defined in so-called
*locales*. Configuration includes, among other things, settings for date and
currency format, the set of characters in use and the language used for
internationalized programs. The installed locales can be changed in the UMC
module :guilabel:`Language settings` under :menuselection:`Language settings -->
Installed system locales`. The standard locale is set under *Default system
locale*.

.. _system-administration-language-settings-figure:

.. figure:: /images/computers_timezone.*
   :alt: Configuring the language settings

   Configuring the language settings

The *Keyboard layout* in the menu entry *Time zone and keyboard settings* is
applied during local logins to the system.

.. _system-administration-time-zone-synchronization:

Time zone and time synchronization
----------------------------------

The time zone in which a system is located can be changed in the UMC module
:guilabel:`Language settings` under :menuselection:`Time zone and keyboard
settings --> Time zone`.

Asynchronous system times between individual hosts of a domain can be the source
of a large number of errors, for example:

* The reliability of log files is impaired.

* Kerberos operation is disrupted.

* The correct evaluation of the validity periods of passwords can be disturbed.

Usually the :term:`Primary Directory Node` functions as the time server of a domain. With the
UCR variables :envvar:`timeserver`, :envvar:`timeserver2` and
:envvar:`timeserver3` external NTP servers can be included as time sources.

Manual time synchronization can be started by the command :command:`ntpdate`.

Windows clients joined in a Samba/AD domain only accept signed NTP time
requests. If the :term:`UCR variable` :envvar:`ntp/signed` is set to ``yes``, the NTP
replies are signed by Samba/AD.
