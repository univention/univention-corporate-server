.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure:

*********************
Domain infrastructure
*********************

This chapter covers the infrastructure foundation of a Nubus for UCS domain.
A Nubus domain relies on multiple systems with different roles and responsibilities.
These systems work together to provide the critical directory, authentication, and management services
that keep your domain operational.

The Primary Directory Node serves as the central hub of your domain,
storing and managing all domain data.
To ensure your domain stays available and resilient,
you need to understand both the different system roles you can deploy
and the strategies for protecting against single points of disruption.

This chapter has the following main sections:

System Roles
    Learn about the different system roles you can deploy in your domain,
    from the critical Primary Directory Node to various client systems.

Redundancy and Failover for the Primary Directory Node
    Explore strategies to protect your domain infrastructure through redundancy and failover mechanisms,
    ensuring continued service availability even if critical systems experience disruption.

.. toctree::

   system-roles
   ha
