.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _management-interface:

********************
Management interface
********************

The *Management UI* is the web-based interface for administering Nubus for UCS.
This chapter covers configuration tasks for technical administrators
who need to control how users sign in, manage licenses, and customize the appearance of the web interfaces.

Authentication
   Configure how users sign in to the *Portal* and the *Management UI*.
   This includes session timeout settings, single sign-on with SAML or OpenID Connect,
   and how to restore standard sign-in if needed.
   See :ref:`management-interface-auth`.

License management
   View, activate, and manage the Nubus for UCS license.
   The license controls access to Univention App Center
   and defines capacity limits for users and clients in your domain.
   See :ref:`management-interface-license`.

Web interface themes
   Switch between the built-in light and dark themes,
   or create a custom theme to match your organization's branding.
   See :ref:`management-interface-theming`.

Directory reports
   Create predefined reports for users, groups, and computers
   directly from the management modules or the command line.
   Customize the report output by replacing the logo or registering new report templates.
   See :ref:`management-interface-directory-reports`.

.. toctree::
   :caption: Contents

   auth
   license
   theme
   directory-reports
