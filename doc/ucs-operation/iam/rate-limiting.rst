.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _iam-rate-limiting:

Rate limiting for exposed APIs
===============================

This section provides a generic, vendor-agnostic starting point
for implementing rate limiting in front of Nubus for UCS APIs and services
that you expose to external networks or third-party software.

.. important::

   Nubus for UCS doesn't ship rate limiting for its APIs and services.
   If you expose an API externally,
   you're responsible for adding a reverse proxy, API gateway,
   or comparable component that enforces rate limiting.

   This section doesn't recommend specific rate-limit thresholds.
   Appropriate values depend on your expected traffic, the API's capacity,
   and your risk tolerance.

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-rate-limiting`
      in :cite:t:`uv-nubus-manual`
      for the list of Nubus APIs and services that need rate limiting
      when exposed externally,
      and their default exposure and authentication
      in Nubus for Kubernetes and Nubus for UCS.

.. _iam-rate-limiting-why:

What rate limiting protects against
--------------------------------------

Rate limiting in front of an exposed API is a compliance and hardening measure
against unauthorized automated use, such as:

Credential stuffing and password guessing
   Automated, high-volume attempts to authenticate,
   for example, against the Keycloak token endpoint, if you install and activate it,
   or against sign-in on the *Management UI*.

Scraping and data harvesting
   Automated, high-volume read requests against APIs that return directory or portal data.

Denial of service through resource exhaustion
   A high volume of requests, legitimate or not,
   that degrades the service for other users.

.. _iam-rate-limiting-approach:

Generic implementation approach
-----------------------------------

Implement rate limiting at the HTTP proxy or gateway layer,
in front of Nubus for UCS,
rather than inside the individual components.
This keeps the enforcement point independent of the application
and lets you apply the same mechanism consistently across multiple exposed APIs.

Consider the following aspects when you design your rate limiting:

Identify the client
   Rate limit per client IP address for anonymous or pre-authentication traffic,
   such as sign-in requests.
   For already-authenticated traffic,
   consider rate limiting per authenticated identity in addition to,
   or instead of, the client IP address.
   Per-identity limiting avoids one shared network address, for example, behind a NAT gateway,
   penalizing every user behind it.

Distinguish expensive and sensitive endpoints from cheap ones
   Apply stricter limits to endpoints that perform authentication,
   change state, or are computationally expensive,
   such as sign-in, password reset, or the UDM HTTP REST API.
   Apply more permissive limits to inexpensive, read-only endpoints.

Allow for legitimate bursts
   A limit that only considers a long-term average request rate
   can still allow a damaging short burst of requests,
   while a limit that's too strict for short bursts
   can reject legitimate usage patterns, such as a client retrying after a network hiccup.
   Most reverse proxies let you configure both a sustained rate and a burst allowance.

Respond consistently
   When you reject a request because it exceeds the limit,
   respond with the HTTP status code ``429 Too Many Requests``,
   and, where your proxy supports it,
   a ``Retry-After`` header that tells the client when to retry.
   This lets well-behaved clients back off correctly,
   instead of retrying immediately and adding to the load.

Exempt trusted, internal traffic where appropriate
   The *End User Self Service* already distinguishes trusted internal callers from external ones
   for its own rate limiting,
   through :envvar:`umc/self-service/rate-limit/trusted-hosts`.
   Apply the same principle at your proxy:
   don't rate limit traffic that originates from inside your own infrastructure
   the same way you rate limit traffic from the internet.

   .. seealso::

      :ref:`end-user-self-service`
         for information about the *End User Self Service*.

Combine rate limiting with account lockout
   Rate limiting throttles request volume;
   it doesn't replace account lockout after repeated failed sign-in attempts,
   which Nubus for UCS supports as an opt-in, separate mechanism.

   .. seealso::

      :ref:`iam-user-lockout`
         for how to configure account lockout for the PAM stack, Samba and Active Directory,
         and OpenLDAP.

.. _iam-rate-limiting-example:

Illustrative example
------------------------

Nubus for UCS serves its HTTP APIs and the *Management UI*
through the system's Apache HTTP Server,
under the ``/univention/`` path.
Apache doesn't enforce rate limiting by default.

.. important::

   The following describes the *shape* of an implementation,
   not concrete values or a specific product recommendation.
   Determine an appropriate approach and values for your environment
   based on the expected legitimate traffic and the capacity of the backing service.

To add rate limiting, choose one of the following approaches:

Place a reverse proxy or load balancer in front of the system
   Route external traffic through a reverse proxy, load balancer, or API gateway
   that enforces rate limiting,
   using the principles in :ref:`iam-rate-limiting-approach`,
   before it reaches the system's Apache HTTP Server.
   This keeps the enforcement independent of Nubus for UCS
   and works the same way regardless of which product you choose.

Extend the system's Apache configuration
   Alternatively,
   add a third-party Apache module that provides rate limiting or connection limiting,
   such as :program:`mod_evasive` or :program:`mod_qos`.
   These modules aren't part of the default Nubus for UCS installation.
   Verify packaging and compatibility for your UCS version,
   and test the configuration in a non-production environment first.

.. _iam-rate-limiting-monitoring:

Monitor and alert on throttling
-----------------------------------

Configure your reverse proxy or API gateway to log rejected requests,
and monitor the resulting ``429`` responses.
A sudden increase in throttled requests against a specific API
is itself a useful signal of an ongoing automated abuse attempt,
even if the rate limit successfully protects the backing service.
Without this visibility, you only prevent the immediate impact
and miss the opportunity to investigate and respond to the attempt.

.. _iam-rate-limiting-non-http:

Non-HTTP protocols
----------------------

This guide covers rate limiting at the HTTP proxy layer.
LDAP is an exception:
it isn't an HTTP API, so an HTTP proxy doesn't apply to it.
If you expose LDAP externally,
use network-level controls instead,
such as firewall rules that only allow a limited set of remote networks, a VPN,
or connection-count limiting at your load balancer or an LDAP-aware proxy.

.. seealso::

   :ref:`iam-user-lockout-openldap`
      for how to configure account lockout after repeated failed LDAP binds,
      through an OpenLDAP password policy.
