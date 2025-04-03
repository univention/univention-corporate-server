.. SPDX-FileCopyrightText: 2025 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-config-reference:

*********************
Configuration options
*********************

The following files in JSON format define the default roles and custom roles:

:file:`/usr/share/univention-directory-manager-modules/umc-udm-roles.json`
   Contains the default roles ``domainadmin`` and ``ouadmin``:

   .. important::

      Don't change this file.
      UCS updates overwrite it.

:file:`/etc/umc-udm-roles.json`
   Can contain custom role definitions.

   This file doesn't exist by default.
   However, you can create this file
   and add custom role definitions.
   The structure of the file may change at any time.
   If you have multiple servers in your test environment,
   you have to manually keep this file in synchronization between servers.

The following references show the available settings for delegative administration:

.. envvar:: umc/udm/delegation

   Activate or deactivate delegative administration for UMC.

   Possible values:
      ``true`` or ``false``.
