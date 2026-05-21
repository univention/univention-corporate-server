.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _lifecycle-versioning:

Nubus for UCS versioning
========================

Nubus for UCS follows a structured release and versioning strategy to provide system
administrators with predictable update cycles and clear compatibility guidelines.

For information on the scripts
that run during the update process,
see :ref:`lifecycle-perform-updates`.

.. _lifecycle-versioning-numbering-scheme:

Understand version numbering
----------------------------

Nubus for UCS version numbers consist of three parts: ``[Major].[Minor]-[Patch level]``.

For example, Nubus for UCS 5.3-4 is the fourth patch level release of the second minor
update for major release Nubus for UCS 5. This scheme helps you identify which updates
apply to your systems and track compatibility.

.. _lifecycle-versioning-release-types:

Distinguish release types and cycles
------------------------------------

Univention releases four types of updates on different schedules:

.. _lifecycle-versioning-release-types-major:

Major releases
    Appear approximately every 3-4 years
    and introduce significant changes to services, functioning, and software.

.. _lifecycle-versioning-release-types-minor:

Minor releases
    Published approximately every 10-12 months during the maintenance period of a major release.
    They include bug fixes, new features, and product expansion
    and maintain backward compatibility where possible.
    See the Release Notes for behavior changes.

.. _lifecycle-versioning-release-types-patch:

Patch level releases
    Published approximately every 3 months.
    They combine all errata updates into a single, tested release.

.. _lifecycle-versioning-release-types-errata:

Errata updates
    Published continuously during the maintenance period of a minor release.
    They provide security fixes, bug fixes, and small enhancements.
    Errata updates target specific minor releases, such as Nubus for UCS 5.3,
    and you can install them on any patch level release.
    See https://errata.software-univention.de/ for an overview.

.. _lifecycle-versioning-update-hierarchy:

Understanding the update hierarchy
----------------------------------

The four update types form a structured hierarchy:

* Major releases enter a maintenance period during which Univention issues
  minor releases every 10-12 months.

* Minor releases receive continuous errata updates addressing security
  vulnerabilities, bugs, and small enhancements.

* Errata updates target specific minor releases
  and you can install them on any
  patch level release of that minor release.

* Every 3 months, Univention bundles accumulated errata updates into a patch level release,
  providing a regular checkpoint for testing and deployment.

This ensures predictable cycles: major versions every 3-4 years, minor versions
every 10-12 months, patch level releases every 3 months, and errata updates continuously.

.. _lifecycle-versioning-maintenance-periods:

Plan for support and maintenance periods
----------------------------------------

Each major release has defined support and maintenance periods determining how
long it receives updates. The *maintenance period* is when Univention issues
minor releases, patch level releases, and errata updates for a major release.

.. _lifecycle-versioning-stay-informed:

Stay informed about updates
---------------------------

When new releases or errata updates are available,
you can receive notifications through the following:

Management UI notifications
    The system displays a notification
    when you open a management module in the *Management UI*
    if updates are available.

Email notifications
    Subscribe to release and errata update newsletters separately to stay
    informed about updates relevant to your infrastructure.

Changelog documents
    Univention publishes a changelog document for every release update, listing
    updated packages, error corrections, new functions,
    and references to Univention Bugzilla.

.. seealso::

   For specific maintenance timelines and end-of-life dates, see the
   :external+uv-docs-overview:ref:`UCS Maintenance Information <maintenance-ucs>`.

   For detailed release information, see the
   :external+uv-docs-overview:ref:`Nubus for UCS Release Notes <release-notes>`.

   To subscribe to newsletters, visit the
   `Univention Newsletter <https://www.univention.com/about-us/newsletter/>`_.
