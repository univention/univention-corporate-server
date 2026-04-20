.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _introduction:

************
Introduction
************

.. important::

   Univention is actively migrating sections of this manual to the
   :cite:t:`uv-ucs-operation`.
   For each moved section, you find a link to its new location
   in that document.
   If you don't find the content you're looking for here,
   check :cite:t:`uv-ucs-operation` directly.

The content of this section moved to
:external+uv-ucs-operation:ref:`intro`
in :cite:t:`uv-ucs-operation`.

.. _introduction-what-is-ucs:

What is Univention Corporate Server?
====================================

The content of this section moved to
:external+uv-ucs-operation:ref:`intro-understanding-nubus-for-ucs-whats-ucs`
in :cite:t:`uv-ucs-operation`.

.. _introduction-nubus:

What is Univention Nubus?
=========================

The content of this section moved to
:external+uv-ucs-operation:ref:`intro-understanding-nubus-for-ucs`
in :cite:t:`uv-ucs-operation`.

.. _introduction-overview-ucs:

Overview of UCS
===============

The content of this section moved to
:external+uv-ucs-operation:ref:`intro-key-concepts`
in :cite:t:`uv-ucs-operation`.

.. _introduction-commissioning:

Commissioning
-------------

The content of this section moved to
:external+uv-ucs-operation:ref:`intro-key-concepts`
in :cite:t:`uv-ucs-operation`.

.. _introduction-domain-concept:

Domain concept
--------------

The content of this section moved to
:external+uv-ucs-operation:ref:`intro-domain-concept`
in :cite:t:`uv-ucs-operation`.

.. _introduction-expandability-with-components:

Expandability with the Univention App Center
--------------------------------------------

The content of this section moved to
:external+uv-ucs-operation:ref:`intro-app-center`
in :cite:t:`uv-ucs-operation`.

.. _introduction-ldap-directory-service:

LDAP directory service
----------------------

The content of this section moved to
:external+uv-ucs-operation:ref:`intro-ldap-directory-service`
in :cite:t:`uv-ucs-operation`.

.. _introduction-domain-administration:

Domain administration
---------------------

The content of this section moved to
:external+uv-ucs-operation:ref:`intro-management-ui`
in :cite:t:`uv-ucs-operation`.

.. _introduction-computer-administration:

Computer administration
-----------------------

The content of this section moved to
:external+uv-ucs-operation:ref:`intro-key-concepts`
in :cite:t:`uv-ucs-operation`.

.. _introduction-policy-concept:

Policy concept
--------------

The content of this section moved to
:external+uv-ucs-operation:ref:`intro-policy-concept`
in :cite:t:`uv-ucs-operation`.

.. _introduction-listener-notifier-replication:

Listener/notifier replication
-----------------------------

The content of this section moved to
:external+uv-ucs-operation:ref:`intro-listener-notifier-replication`
in :cite:t:`uv-ucs-operation`.

.. _introduction-further-documentation:

Further documentation
=====================

This manual addresses just a small selection of the possibilities in
UCS. Among other things, UCS and solutions based on UCS provide:

* Comprehensive support for complex server environments and replication
  scenarios

* Advanced capabilities for Windows environments

* Central network management with DNS and DHCP

* Monitoring systems and networks

* Print server functionalities

* Proxy server

Further documentation related to UCS and further issues is published under
:cite:t:`ucs-docs`.

.. _introduction-symbols-and-conventions-used-in-this-manual:

Symbols and conventions used in this manual
===========================================

The manual uses the following symbols:

.. caution::

   Warnings are highlighted.

.. note::

   Notes are also highlighted.

This table describes the functionality of a UMC module:

.. table:: Tab DHCP service

   +-----------------------+-----------------------------------------------+
   | Attribute             | Description                                   |
   +=======================+===============================================+
   | Name                  | The unique name of a DHCP service.            |
   +-----------------------+-----------------------------------------------+
   | Description           | An arbitrary description of the service.      |
   +-----------------------+-----------------------------------------------+

Menu entries, button labels, and similar details with actions are printed in
:guilabel:`this font face`.

*Names* are highlighted.

``Computer names, LDAP DNs``, :command:`program
names`, :file:`file names, file paths`,
`internet addresses <https://example.com>`_ and ``options`` are
also optically accented.

``Commands and other keyboard input`` is accented optically.

.. code-block:: console

   In addition, excerpts from configuration files, screen output, etc. are
   printed as code block.

A backslash (``\``) at the end of a line signifies that the subsequent line
feed is not to be understood as an *end of line*.
This circumstance may occur, for example, where commands cannot be
represented in one line in the manual, yet have to be entered in the
command line in one piece without the backslash or with the backslash
and a subsequent :kbd:`Enter`.

The path to a function is represented in a similar way to a file path.
:menuselection:`Users --> Add` means for example, you have to click
:guilabel:`Users` in the main menu and :guilabel:`Add` in the submenu.
