.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _iam-last-bind:

Track last sign-in time to detect inactive accounts
===================================================

Inactive user accounts are a security risk
because attackers can compromise them without anyone noticing.
By recording when each account last signed in,
you can identify accounts that haven't signed in recently
and take appropriate action.

Read this page to learn how to:

* activate the OpenLDAP ``lastbind`` overlay module.
* collect sign-in timestamps from all LDAP servers in the domain.
* schedule automatic updates to keep the timestamps current.

.. caution::
   Before using this feature, read :uv:kb:`knowledge base article about
   activating the OpenLDAP lastbind overlay module <14404>`.

.. _iam-last-bind-activate:

Activate the overlay module
---------------------------

The `lastbind overlay module <https://manpages.debian.org/bookworm/slapd/slapo-lastbind.5.en.html>`_
for OpenLDAP records when a user last signed in,
storing the result in the ``authTimestamp`` attribute.
Use these timestamps to identify accounts that haven't signed in recently.

When you set the :term:`UCR variable` :envvar:`ldap/overlay/lastbind` to ``yes``
and restart the OpenLDAP server,
the ``lastbind`` overlay module activates.
To restart the OpenLDAP server,
run the command in :numref:`iam-last-bind-activate-listing`.
The module writes a timestamp to the account's ``authTimestamp`` attribute
each time that account performs an LDAP bind.
:envvar:`ldap/overlay/lastbind/precision` sets
the minimum time in seconds between updates to the ``authTimestamp`` attribute.
This prevents excessive write operations that impair performance.

.. code-block:: console
   :caption: Restart the OpenLDAP server
   :name: iam-last-bind-activate-listing

   $ systemctl restart slapd

.. _iam-last-bind-collect:

Collect and store the timestamp
-------------------------------

The ``lastbind`` overlay module only writes ``authTimestamp`` to the local LDAP server.
Other LDAP servers don't replicate this attribute.
For that reason,
run the :file:`/usr/share/univention-ldap/univention_lastbind.py` script.
The script collects the most recent ``authTimestamp`` value
from all reachable LDAP servers in the Nubus for UCS domain
and stores it in the ``lastbind`` extended attribute.

The ``lastbind`` extended attribute
stores its value in the ``univentionAuthTimestamp`` LDAP attribute,
which you can query directly in the directory.

.. _iam-last-bind-schedule:

Schedule automatic updates
--------------------------

To keep the ``lastbind`` extended attribute up to date,
create a cron job using UCR as shown in :numref:`iam-last-bind-schedule-listing`.

For more information, see :external+uv-ucs-manual:ref:`computers-defining-cron-jobs-in-univention-configuration-registry`
in :cite:t:`ucs-manual`.

.. code-block:: console
   :caption: Create cron job to regularly update the ``lastbind`` extended attribute
   :name: iam-last-bind-schedule-listing

   $ ucr set cron/update_lastbind_attribute/command='\
   /usr/share/univention-ldap/univention_lastbind.py --allusers'\
     cron/update_lastbind_attribute/time='00 06 * * *'
   # daily at 06:00
