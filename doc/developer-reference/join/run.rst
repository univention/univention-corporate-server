.. _join-run:

Running join scripts
====================

.. index::
   single: domain join; running

The following commands related to running join scripts exist:

:command:`univention-join`
   When :command:`univention-join` is invoked, the machine account is created, if
   it is missing. Otherwise an already existing account is re-used which allows
   it to be created beforehand. The distinguished name (dn) of that entry is
   stored locally in the |UCSUCRV| :envvar:`ldap/hostdn`. A random password is
   generated, which is stored in the file :file:`/etc/machine.secret`.

   After that the file :file:`/var/univention-join/status` is cleared and all
   join scripts located in :file:`/usr/lib/univention-install/` are executed in
   lexicographical order.

:command:`univention-run-join-scripts`
   This command is similar to :command:`univention-join`, but skips the first
   step of creating a machine account. Only those join scripts are executed,
   whose current version is not yet registered in
   :file:`/var/univention-join/status`.

:command:`univention-check-join-status`
   This command only checks for join scripts in
   :file:`/usr/lib/univention-install/`, whose version is not yet registered in
   :file:`/var/univention-join/status`.

When packages are installed, it depends on the server role, if join scripts are
invoked automatically from the ``postinst`` Debian maintainer script or not.
This only happens on |UCSPRIMARYDN| and |UCSBACKUPDN| system roles, where the
local ``root`` user has access to the file containing the LDAP credentials. On
all other system roles the join scripts need to be run manually by invoking
:command:`univention-run-join-scripts` or doing so through UMC.
