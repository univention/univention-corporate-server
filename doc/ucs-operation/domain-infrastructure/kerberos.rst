.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure-kerberos:

Kerberos
========

Nubus for UCS uses Kerberos to authenticate users and services across your domain.
This section covers how Kerberos works,
how you configure the realm,
and how Nubus for UCS implements it.

.. _domain-infrastructure-kerberos-overview:

How Kerberos works
------------------

The *Key Distribution Center* (KDC) is the central trust authority in a Kerberos network.
When you sign in,
the KDC issues a *ticket* that grants access to other services inside the Kerberos realm.

Tickets are valid for 8 hours by default.

.. important::

   All systems in the Kerberos realm must have synchronized clocks.
   Clock skew causes authentication failures.

.. _domain-infrastructure-kerberos-realm:

Kerberos realm
--------------

The Kerberos realm name derives from your domain name.
The installer stores it in the :term:`UCR variable` :envvar:`kerberos/realm`.

.. warning::

   You can't change the Kerberos realm name after installation.
   Choose your realm name carefully.

.. _domain-infrastructure-kerberos-implementation:

Kerberos implementation in Nubus for UCS
-----------------------------------------

Nubus for UCS uses the Heimdal Kerberos implementation.
On UCS directory nodes without Samba/AD,
Heimdal runs as a standalone service.
On Samba/AD domain controllers,
Samba provides Kerberos through its built-in Heimdal version.

Both UCS directory nodes and Samba/AD domain controllers access the same Kerberos data.
The Univention S4 connector synchronizes between Samba/AD and OpenLDAP.
For more information, see :external+uv-ucs-manual:ref:`windows-s4-connector`.

.. _domain-infrastructure-kerberos-kdc:

KDC selection
-------------

By default,
DNS service records determine which KDC your system uses.
To override the KDC for a specific system,
set the :term:`UCR variable` :envvar:`kerberos/kdc`.

When you install Samba/AD on any domain member,
the DNS service record changes to advertise only the Samba/AD KDCs.
In a mixed environment,
use only the Samba/AD KDCs.

.. _domain-infrastructure-kerberos-administration-server:

Kerberos administration server
------------------------------

The Kerberos administration server runs on the :term:`Primary Directory Node`.
It manages administrative settings for the domain.
Because Nubus for UCS reads most settings directly from the LDAP directory,
the server primarily manages passwords.

Use :command:`kpasswd` to change passwords.
This tool also updates the password in LDAP.

To configure the administration server,
set the :term:`UCR variable` :envvar:`kerberos/adminserver`.
