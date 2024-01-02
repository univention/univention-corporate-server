.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _mail-ox-connector:

OX Connector
============

:program:`OX Connector` is an app in Univention App Center. It synchronizes
selected users and groups to :program:`OX App Suite` and remote installations
like for example a hosted OX App Suite. Starting with :program:`OX Connector`
version ``2.1.2`` and :program:`OX App Suite` version ``7.10.6-ucs4``, the
:program:`OX Connector` integrates with :program:`OX App Suite` from Univention
App Center to provision user and group accounts to :program:`OX App Suite`.

.. warning::

   :program:`OX App Suite` versions older than ``7.10.6-ucs4`` include their own
   synchronization. :program:`OX Connector` doesn't synchronize with those
   versions and you must therefore not use it with the separate :program:`OX App
   Suite` app from the App Center.

.. seealso::

   OX Connector App documentation
      For more information about the :program:`OX Connector`, refer to
      :ref:`limit-ox-app-suite-app` in the dedicated documentation at
      :cite:t:`ox-connector-doc`.
