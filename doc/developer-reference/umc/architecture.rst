.. SPDX-FileCopyrightText: 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _umc-architecture:

Architecture
============

The Univention Management Console service consists of four components.
The communication between these components is encrypted using SSL. The
architecture and the communication channels is shown in
:numref:`umc-api`.

.. _umc-api:

.. figure:: /images/umc-api.*
   :alt: UMC architecture and communication channels

   UMC architecture and communication channels

* The *UMC server* is a small web server that provides HTTP access to the modules and
  manages the connection and verifies that only authorized users gets access.
  It is used by the web frontend.

* The *UMC module* processes are forked by the UMC server to provide a specific
  area of management tasks within a session.
