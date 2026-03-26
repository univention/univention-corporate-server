.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _central-management-umc-introduction:

Introduction
============

.. _central-access:

Access
------

The |UCSWEB| can be opened on any UCS system via the URL
:samp:`https://{servername}/`. Alternatively, access is also possible via the server's
IP address. Under certain circumstances it may be necessary to access the
services over an insecure connection (e.g., if no SSL certificates have been
created for the system yet). In this case, ``http`` must be used instead of
``https`` in the URL. In this case, passwords are sent over the network in plain
text!

.. _central-browser-compatibility:

Browser compatibility
---------------------

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-ui-browser-compatibility`
in :cite:t:`uv-nubus-manual`.

.. _central-theming:

Switching between dark and light theme for |UCSWEB|\ s
------------------------------------------------------

The content of this section moved to
:external+uv-ucs-operation:ref:`management-interface-theming-light-dark`
in :cite:t:`uv-ucs-operation`.

.. _central-theming-custom:

Creating a custom theme/Adjusting the design of |UCSWEB|\ s
-----------------------------------------------------------

The content of this section moved to
:external+uv-ucs-operation:ref:`management-interface-theming-custom`
in :cite:t:`uv-ucs-operation`.

.. _central-management-umc-feedback:

Feedback on UCS
---------------

By choosing the :menuselection:`Help --> Feedback` option in the upper right
menu, you can provide feedback on UCS via a web form.

.. _central-management-umc-matomo:

Collection of usage statistics
------------------------------

Anonymous usage statistics on the use of the |UCSWEB| are collected when using
the *core edition* version of UCS (which is generally used for evaluating UCS).
Further information can be found in :uv:kb:`Data collection in Univention
Corporate Server <6701>`.
