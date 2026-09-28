.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-rate-limiting:

Rate-limiting approaches for externally exposed services
=========================================================

Rate limiting controls how many requests external clients can send within a defined period.
It helps protect externally exposed services from excessive traffic.
The following section describes available rate-limiting approaches for HTTP services in Nubus for UCS.

For general guidance on designing and monitoring rate limits,
see :external+uv-nubus-manual:ref:`nubus-rate-limiting-implementation-guide`
in :cite:t:`uv-nubus-manual`.

.. _system-administration-rate-limiting-http-services:

Rate-limiting approaches for HTTP services
------------------------------------------

Nubus for UCS serves its HTTP APIs and the *Management UI*
through the system's Apache HTTP Server,
under the ``/univention/`` path.
Apache doesn't enforce rate limiting by default.

Consider the following approaches for rate limiting:

Place a reverse proxy or load balancer in front of the HTTP services
   Route external traffic through a reverse proxy, load balancer, or API gateway
   that enforces rate limiting,
   using the principles in :external+uv-nubus-manual:ref:`nubus-rate-limiting-implementation-guide`,
   before it reaches the system's Apache HTTP Server.
   This approach keeps rate-limit enforcement independent of Nubus for UCS.
   Refer to the selected product's documentation for product-specific configuration.

Extend the system's Apache configuration
   Alternatively,
   add a third-party Apache module that provides rate or connection limiting,
   such as ``mod_evasive`` or ``mod_qos``.
   These modules aren't part of the default Nubus for UCS installation.
   Verify that the module is available as a package and compatible with your UCS version,
   and test the configuration in a non-production environment first.
