.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-proxy:

Configure proxy settings through UCR variables
==============================================

This page describes how to configure proxy settings
so that command line tools and system utilities can access web resources through a proxy server.

Many command line tools that access web servers,
such as :command:`wget`, :command:`elinks`, and :command:`curl`,
use the ``http_proxy`` or ``https_proxy`` environment variables
if you set them.
The tools automatically use the proxy server
you've configured in these variables.

.. _system-administration-proxy-configuration:

Configure proxy access
----------------------

To configure these environment variables persistently,
you can use the :term:`UCR variable` :envvar:`proxy/http` and :envvar:`proxy/https`.
The system configures the environment variables in :file:`/etc/profile`
based on these UCR variables.

Specify the proxy URL,
for example :samp:`http://192.0.2.100`.
To add the proxy port, append a colon to the URL,
for example :samp:`http://192.0.2.100:3128`.
If the proxy requires authentication,
include your credentials in the URL like this:
:samp:`http://{<Username>}:{<Password>}@192.0.2.100:3128`.

.. _system-administration-proxy-exclusions:

Exclude domains from proxy access
---------------------------------

To exclude certain domains from proxy access,
list them in the UCR variable :envvar:`proxy/no_proxy`,
separated by commas.
When you exclude a domain,
the exclusion also applies to all its subdomains.
For example, if you exclude ``example.com``,
the system also excludes ``mail.example.com`` and ``www.example.com``.

.. _system-administration-proxy-session-behavior:

Session behavior
----------------

.. important::

   When you change proxy settings,
   existing sessions don't update the environment variables.
   You must sign in again to apply the new settings.

.. _system-administration-proxy-univention-tools:

Integration with Nubus for UCS tools
------------------------------------

The Nubus for UCS tools for software updates,
such as :command:`univention-repository-update`,
also support operation through a proxy.
These tools read the UCR variables
:envvar:`proxy/http`, :envvar:`proxy/https`, and :envvar:`proxy/no_proxy`,
so your proxy configuration applies automatically.

.. seealso::

   For information about software updates,
   see the following resources:

   * :ref:`lifecycle-update-strategies`
   * :ref:`lifecycle-package-installation-management`
