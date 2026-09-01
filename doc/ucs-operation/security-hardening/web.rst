.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _security-hardening-web:

Harden web services
===================

Apache and the Univention Management Console (UMC) expose administration and
user services through HTTP.
Use HTTPS for those services and limit the information that unauthenticated
responses disclose.

.. _security-hardening-web-https:

Enforce HTTPS
-------------

Set the following UCR variables on each system that provides the Apache web
service:

.. code-block:: console

   $ ucr set apache2/force_https=yes
   $ ucr set apache2/hsts=yes
   $ ucr set apache2/ssl/honorcipherorder=yes

``apache2/force_https`` redirects HTTP requests to HTTPS.
``apache2/hsts`` tells browsers to use HTTPS for the configured host.
Enable HSTS only after verifying that every required hostname has a valid
certificate and HTTPS endpoint.
Review ``apache2/force_https/exclude/*`` entries because they intentionally
exclude matching requests from the redirect.

For UMC, also protect the session cookie:

.. code-block:: console

   $ ucr set umc/http/enforce-secure-cookie=true
   $ ucr set umc/http/cookie/samesite=Strict

Use ``Lax`` instead of ``Strict`` only when a required authentication flow
needs cross-site navigation.
Don't use ``None`` unless the cookie is required in a cross-site context and
the HTTPS configuration is reliable.

For session timeout configuration, see
:ref:`management-interface-auth-sign-in-session-timeout`.

.. _security-hardening-web-tls:

Use current TLS versions
------------------------

On environments where all clients support TLS 1.3, enable TLS 1.3-only mode:

.. code-block:: console

   $ ucr set apache2/ssl/tlsv13=yes

This setting excludes clients that support only TLS 1.2.
Test browsers, integrations, monitoring systems, and API clients before
applying it.

Keep TLS compression disabled because it can expose secrets through attacks
such as CRIME:

.. code-block:: console

   $ ucr set apache2/ssl/compression=no

Maintain ``apache2/ssl/ciphersuite`` according to the TLS policy for your
UCS release.
The cipher suite must support the certificates and clients that your
environment requires.

For virtual-host deployments, consider enabling the strict SNI check:

.. code-block:: console

   $ ucr set apache2/ssl/strict-sni-vhost-check=yes

This rejects clients that don't send Server Name Indication.
Test clients that access a named virtual host before applying the setting.

Set a sufficiently long HSTS lifetime after verifying the HTTPS deployment.
For example, 63,072,000 seconds is 2 years:

.. code-block:: console

   $ ucr set apache2/hsts/max-age=63072000

.. _security-hardening-web-disclosure:

Reduce information disclosure
-----------------------------

Apache can disclose product and version details in response headers and error
pages.
Use the following values to reduce reconnaissance information:

.. code-block:: console

   $ ucr set apache2/server-tokens=Prod
   $ ucr set apache2/server-signature=Off

Disable directory listings and remove unused web content, including the
default ``/var/www/html/`` content, when the system doesn't provide it.
Review enabled Apache modules and UserDir configuration as part of the same
service inventory.

The Apache UserDir module publishes user-controlled content through URLs such
as ``/~USERNAME``.
Disable the module when no use case requires it.
Also remove the default Apache icons alias and unused document-root content
when they aren't required by an installed application.

UMC and UDM REST API error responses can disclose implementation details.
Keep traceback and identity-provider error reporting disabled on production
systems:

.. code-block:: console

   $ ucr set umc/http/show_tracebacks=false
   $ ucr set directory/manager/rest/show-tracebacks=false

If you use the Self Service password reset, limit the lifetime of reset
tokens:

.. code-block:: console

   $ ucr set umc/self-service/passwordreset/token_validity_period=900

This value is in seconds.
Short-lived tokens reduce the exposure if a reset token is disclosed, but a
value that is too short can prevent users from completing the reset process.

Keep the UMC ``Server`` response header and reverse-proxy ``Via`` header from
exposing internal product, version, or hostname details where your proxy
configuration permits it.
