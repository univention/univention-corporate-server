.. _domain-listener-notifier:

Listener/notifier domain replication
====================================

.. highlight:: console

.. _domain-listener-notifier-intro:

Listener/notifier replication workflow
--------------------------------------

Replication of the directory data within a UCS domain occurs via the
|UCSUDL|/Notifier mechanism:

* The |UCSUDL| service runs on all UCS systems.

* On the |UCSPRIMARYDN| (and possibly existing |UCSBACKUPDN| systems) the
  |UCSUDN| service monitors changes in the LDAP directory and makes the selected
  changes available to the |UCSUDL| services on the other UCS systems.

.. _domain-join-listener-notifier:

.. figure:: /images/administration-overview.*
   :alt: Listener/Notifier mechanism

   Listener/Notifier mechanism

The active |UCSUDL| instances in the domain connect to a |UCSUDN| service. If
an LDAP change is performed on the |UCSPRIMARYDN| (all other LDAP servers in the
domain are read-only), this is registered by the |UCSUDN| and notified to the
listener instances.

Each |UCSUDL| instance uses a range of |UCSUDL| modules. These modules are
shipped by the installed applications; the print server package includes, for
example, listener modules which generate the CUPS configuration.

|UCSUDL| modules can be used to communicate domain changes to services which are
not LDAP-compatible. The print server CUPS is an example of this: The printer
definitions are not read from the LDAP, but instead from the
:file:`/etc/cups/printers.conf` file. Now, if a printer is saved in the UMC
printer management, it is stored in the LDAP directory. This change is detected
by the |UCSUDL| module *cups-printers* and an entry added to, modified or
deleted in :file:`/etc/cups/printers.conf` based on the data in the LDAP.

Additional information on the setup of |UCSUDL| modules and developing your own
modules can be found in `Univention Developer Reference
<https://docs.software-univention.de/developer-reference-5.0.html>`_.

LDAP replication is also performed by a listener module. If the LDAP server to
be replicated to is not accessible, the LDAP changes are temporarily stored in
the :file:`/var/lib/univention-directory-replication/failed.ldif` file. The
contents of the file are automatically transferred to the LDAP when the LDAP
server is available again.

The listener/notifier mechanism works based on transactions. A transaction ID is
increased for every change in the LDAP directory of the |UCSPRIMARYDN|. A
|UCSUDL| instance which has missed several transactions - for example, because
the computer was switched off - automatically requests all the missing
transactions once the connection is available again until its local transaction
ID corresponds to that of the |UCSPRIMARYDN|.

.. _domain-listener-notifier-erroranalysis:

Analysis of listener/notifier problems
--------------------------------------

.. _domain-listener-notifier-erroranalysis-debug:

Log files/debug level of replication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All status messages from the |UCSUDL| and the executed listener modules
are logged in the
:file:`/var/log/univention/listener.log` file. The level
of detail of the log messages can be configured using the |UCSUCRV|
:envvar:`listener/debug/level`.

Status messages from the |UCSUDN| service are logged in the
:file:`/var/log/univention/notifier.log` file. The debug level can be configured
using the :envvar:`notifier/debug/level`.

.. _domain-listener-notifier-erroranalysis-replication:

Identification of replication problems
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the domain replication is running normally (normal system load, no network
problems), the delay between changes being made in UMC modules and these changes
being replicated to, for example, a |UCSREPLICADN| is barely noticeable. An
incomplete replication can be identified by comparing the transaction IDs of the
listener and notifier services.

The transactions registered by the notifier service are written in the
:file:`/var/lib/univention-ldap/notify/transaction` file in ascending order on
the |UCSPRIMARYDN|. An example:

.. code-block::

   root@primary:~# tail -1 /var/lib/univention-ldap/notify/transaction
   836 cn=replica3,cn=dc,cn=computers,dc=firma,dc=de m


The last transaction received by the listener system is stored in the
:file:`/var/lib/univention-directory-listener/notifier_id` file:

.. code-block::

   root@replica1:~# cat /var/lib/univention-directory-listener/notifier_id
   836


This check can also be performed automatically by the Nagios service
``UNIVENTION_REPLICATION`` (see :ref:`nagios-preconfigured-checks`).

.. _domain-listener-notifier-erroranalysis-reinit:

Reinitialization of listener modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If there are problems in running a listener module, there is the option of
reinitializing the module. In this case, all LDAP objects with which the
listener module works are passed on again.

The name of the listener module must be supplied to the command for the renewed
initialization. The installed listener modules can be found in the
:file:`/var/lib/univention-directory-listener/handlers/` directory.

The following command can be used to reinitialize the printer module, for
example:

.. code-block::

   $ univention-directory-listener-ctrl resync cups-printers


