.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _lifecycle-repository-management:

Repository management
=====================

Repository management involves two interconnected decisions:
creating a local repository
and configuring your systems to use it.
Together, these decisions give you control over system updates.
This section covers the repository management workflow,
from setting up a local repository to maintaining it over time.

To create a local repository,
synchronize packages from upstream Univention servers
to your local infrastructure.
After you have a local repository,
you configure your systems to use it
instead of reaching out to remote servers.
These two steps are separate but deeply connected—you need both to manage updates independently.

This section covers three main topics:
creating and updating a local repository,
configuring your systems to use it,
and maintaining it for long-term stability.
