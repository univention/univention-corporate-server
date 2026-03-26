.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _central-user-interface:

|UCSUMC| modules
================

|UCSUMC| (UMC) modules are the web-based tool for administration of the UCS
domain. They are shown on the portal page (:ref:`central-portal`) for logged in
administrators. Depending on the system role, different UMC modules are
available. Additionally installed software components may bring their own new
UMC modules.

UMC modules for the administration of all the data included in the LDAP
directory (such as users, groups and computer accounts) are only provided on
|UCSPRIMARYDN|\ s and |UCSBACKUPDN| s. Changes made in these modules are applied
to the whole domain.

UMC modules for the configuration and administration of the local system are
provided on all system roles. These modules can for example be used to install
additional applications and updates, adapt the local configuration via |UCSUCR|
or start/stop services.

.. _central-license:

Activation of UCS license / license overview
--------------------------------------------

The content of this section moved to
:external+uv-ucs-operation:ref:`management-interface-license`
in :cite:t:`uv-ucs-operation`.

.. _central-management-umc-operating-instructions-for-domain-modules:

Operating instructions for modules to administrate LDAP directory data
----------------------------------------------------------------------

All UMC modules for managing LDAP directory objects such as user, group
and computer accounts or configurations for printers, shares, mail and
policies are controlled identically from a structural perspective. The
following examples are presented using the user management but apply
equally for all modules. The operation of the DNS and DHCP modules is
slightly different. Further information can be found in
:ref:`ip-config-dns-umc` and :ref:`networks-dhcp-general`.

.. _umc-modules:

.. figure:: /images/umc-favorites-tab.*
   :alt: Module overview

   Module overview

The configuration properties/possibilities of the modules are described in the
following chapters:

* Users - :ref:`users-general`

* Groups - :ref:`groups`

* Computers - :ref:`computers-general`

* Networks - :ref:`networks-general`

* DNS - :ref:`networks-dns`

* DHCP - :ref:`module-dhcp-dhcp`

* Shares - :ref:`shares-general`

* Printers - :ref:`print-general`

* Email - :ref:`mail-general`

* Nagios - :ref:`nagios-general`

The use of policies (:ref:`central-policies`) and the LDAP navigation
(:ref:`central-navigation`) are described separately.

.. _umc-usage-search:

Searching for objects
~~~~~~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-ui-management-modules-operations-search`
in :cite:t:`uv-nubus-manual`.

.. _central-management-umc-create:

Creating objects
~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-ui-management-modules-operations-create`
in :cite:t:`uv-nubus-manual`.

.. _central-user-interface-edit:

Editing objects
~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-ui-management-modules-operations-edit`
in :cite:t:`uv-nubus-manual`.

.. _central-user-interface-remove:

Deleting objects
~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-ui-management-modules-operations-delete`
in :cite:t:`uv-nubus-manual`.

.. _central-user-interface-move:

Moving objects
~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-ui-management-modules-operations-move`
in :cite:t:`uv-nubus-manual`.

.. _central-management-umc-notifications:

Display of system notifications
-------------------------------

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-ui-notifications`
in :cite:t:`uv-nubus-manual`.
