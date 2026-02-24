.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-proxy:

Proxy access configuration
==========================

The majority of the command line tools which access web servers (e.g.,
:command:`wget`, :command:`elinks` or :command:`curl`) check whether the
environment variables :envvar:`http_proxy` or :envvar:`https_proxy` are set. If this is the case, the proxy
server set in these variables is used automatically.

The |UCSUCRV| :envvar:`proxy/http` and :envvar:`proxy/https` can also be used to activate the setting of
these environment variables through an entry in :file:`/etc/profile`.

The proxy URL must be specified for this, for example :samp:`http://192.0.2.100`. The
proxy port can be specified in the proxy URL using a colon, for example
:samp:`http://192.0.2.100:3128`. If the proxy requires authentication,
this can be provided in the form :samp:`http://{username}:{password}@192.0.2.100`.

The environment variable is not adopted for sessions currently opened. A new login
is required for the change to be activated.

The Univention tools for software updates also support operation via a proxy and
query the |UCSUCR| variable.

Individual domains can be excluded from use by the proxy by including them
separated by commas in the |UCSUCRV| :envvar:`proxy/no_proxy`. Subdomains are
taken into account; e.g. an exception for ``software-univention.de`` also
applies for ``updates.software-univention.de``.
