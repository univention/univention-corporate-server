.. _chap-listener:

********
|UCSUDL|
********

.. index::
   single: directory listener
   see: listener; directory listener
   see: |UCSUDL|; directory listener

Replication of the directory data within a UCS domain is provided by the
Univention Directory Listener/Notifier mechanism:

* The |UCSUDL| service runs on all UCS systems.

* On the |UCSPRIMARYDN| (and possibly existing |UCSBACKUPDN| systems) the
  |UCSUDN_e| service monitors changes in the LDAP directory and makes the
  selected changes available to the |UCSUDL| services on all UCS systems joined
  into the domain.

The active |UCSUDL| instances in the domain connect to a |UCSUDN| service. If an
LDAP change is performed on the |UCSPRIMARYDN| (all other LDAP servers in the
domain are read-only), this is registered by the |UCSUDN| and reported to the
listener instances.

Each |UCSUDL| instance hosts a range of |UCSUDL| modules. These modules are
shipped by the installed applications; the print server package includes, for
example, listener modules which generate the CUPS configuration.

|UCSUDL| modules can be used to communicate domain changes to services which are
not LDAP-aware. The print server CUPS is an example of this: The printer
definitions are not read from the LDAP, but instead from the file
:file:`/etc/cups/printers.conf`. Now, if a printer is saved in the printer
management of the |UCSUMC|, it is stored in the LDAP directory. This change is
detected by the |UCSUDL| module *cups-printers* and an entry gets added to,
modified in or deleted from :file:`/etc/cups/printers.conf` based on the
modification in the LDAP directory.

By default the Listener loads all modules from the directory
:file:`/usr/lib/univention-directory-listener/system/`. Other directories can be
specified using the option ``-m`` when starting the
:command:`univention-directory-listener` daemon.

.. toctree::

   structure
   api
   module
   tasks-examples
   details
