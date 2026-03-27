.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _udm-blocklists:

Prevent reuse of user property values
=====================================

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-blocklists`
in :cite:t:`uv-nubus-manual`.

.. _udm-blocklists-activate:

Activate block lists
--------------------

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-blocklists-activate`
in :cite:t:`uv-nubus-manual`.

.. _udm-blocklists-configure:

Configure block lists
---------------------

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-blocklists-configure`
in :cite:t:`uv-nubus-manual`.

.. _udm-blocklists-entry-manage:

Manage block list entries
-------------------------

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-blocklists-manage`
in :cite:t:`uv-nubus-manual`.

.. _udm-blocklists-expired-entries:

Expired block list entries
--------------------------

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-blocklists-expired-entries`
in :cite:t:`uv-nubus-manual`.

.. _udm-blocklists-ldap-acl:

LDAP ACLs for block lists
-------------------------

By default, every UCS node in the domain and every member of the
``Domain Admins`` group can write block list entries. And everybody can read.
You can configure the permissions
on the |UCSPRIMARYDN| and the |UCSBACKUPDN|\ s with the following |UCSUCRVs|:

* :envvar:`ldap/database/internal/acl/blocklists/groups/read`
* :envvar:`ldap/database/internal/acl/blocklists/groups/write`

For example, if you want to give a user the permission to delete block list entries
who isn't member of the ``Domain Admins`` group,
you need to create a group with that user as member
and add the LDAP DN of this group to :envvar:`ldap/database/internal/acl/blocklists/groups/write`.
