.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure-udm-blocklists:

Prevent reuse of user property values
=====================================

To prevent reuse of user property values
Nubus for Kubernetes provides the *Blocklists* management module.
For general information about the module,
how to activate and configure block lists,
and how to manage block list entries,
see :external+uv-nubus-manual:ref:`nubus-domain-blocklists`.

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
