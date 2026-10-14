.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure-udm-blocklists:

Prevent reuse of user property values
=====================================

To prevent reuse of user property values,
Nubus for Kubernetes provides the *Blocklists* management module.
For general information about the module,
how to activate and configure block lists,
and how to manage block list entries,
see :external+uv-nubus-manual:ref:`nubus-domain-blocklists`
in :cite:t:`uv-nubus-manual`.

By default, every UCS node in the domain
and every member of the ``Domain Admins`` group
can write block list entries, and all users can read them.
You can configure the permissions
on the :term:`Primary Directory Node`
and the :term:`Backup Directory Nodes <Backup Directory Node>`
with the following :term:`UCR variables <UCR variable>`:

* :envvar:`ldap/database/internal/acl/blocklists/groups/read`
* :envvar:`ldap/database/internal/acl/blocklists/groups/write`

For example, if you want to give a user
who isn't a member of the ``Domain Admins`` group
permission to delete block list entries,
create a group that includes the user
and add the group's LDAP DN to
:envvar:`ldap/database/internal/acl/blocklists/groups/write`.
