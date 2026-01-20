.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _deployment-after-installation:

Steps after the installation
============================

After completing the Nubus for UCS installation,
you can immediately access the *Portal*
and perform essential first tasks.
This section covers only the immediate steps
you can take right now.
More comprehensive configuration and management topics follow in later sections.

.. _deployment-after-installation-open-portal:

Open the portal
---------------

To open the *Portal* in Nubus for UCS,
choose any UCS system in your Nubus for UCS domain
and enter its fully qualified hostname into the browser address bar.
Your client must be able to resolve the hostname through DNS.
If your client can't resolve the DNS name,
you can use the IP address.

The ``root`` and ``Administrator`` users can sign in to the *Portal*,
see :external+uv-nubus-manual:ref:`nubus-portal`
in :cite:t:`uv-nubus-manual`.

.. _deployment-after-installation-license-import:

License import after installation
---------------------------------

If you installed the system as the first system in the Nubus for UCS domain
in the :term:`UCS Primary Directory Node` role,
you can import the license for the domain,
see :external+uv-ucs-manual:ref:`central-license`
in :cite:t:`ucs-manual`.
