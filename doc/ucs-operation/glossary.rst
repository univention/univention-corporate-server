.. SPDX-FileCopyrightText: 2025 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _glossary:

********
Glossary
********

.. glossary::
   :sorted:

   Backup Directory Node
   UCS Backup Directory Node
      The Backup Directory Node is a system role in Nubus for UCS.
      It has a complete read-only copy of the domain database including the
      security certificates.
      Administrators can promote the role to a :term:`Primary Directory Node`.
      For more information about the role concept in Nubus for UCS,
      see :external+uv-architecture:ref:`concept-role`
      in :cite:t:`ucs-architecture`.

   Managed Node
   UCS Managed Node
      The Managed Node is a system role in Nubus for UCS.
      It has no copy of the domain database.
      For more information about the role concept in Nubus for UCS,
      see :external+uv-architecture:ref:`concept-role`
      in :cite:t:`ucs-architecture`.

   Primary Directory Node
   UCS Primary Directory Node
      The Primary Directory Node is a system role in Nubus for UCS.
      It's the first, the primary, domain node in a domain.
      For more information about the role concept in Nubus for UCS,
      see :external+uv-architecture:ref:`concept-role`
      in :cite:t:`ucs-architecture`.

   Replica Directory Node
   UCS Replica Directory Node
      The Replica Directory Node is a system role in Nubus for UCS.
      It has a complete ready-only copy of the domain database,
      or it can have only a subset of the domain database through selective replication.
      For more information about the role concept in Nubus for UCS,
      see :external+uv-architecture:ref:`concept-role`
      in :cite:t:`ucs-architecture`.

