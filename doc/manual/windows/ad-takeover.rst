.. _windows-ad-takeover:

Migrating an Active Directory domain to UCS using Univention AD Takeover
========================================================================

UCS supports the takeover of user, group and computer objects as well as Group
Policy Objects (GPOs) from a Microsoft Active Directory (AD) domain. Windows
clients do not need to rejoin the domain. The takeover is an interactive process
consisting of three distinct phases:

#. Copy all objects from Active Directory to UCS

#. Copy of the group policy files from the AD server to UCS

#. Deactivate the AD server and assign all FSMO roles to the UCS DC

The following requirements must be met for the takeover:

* The UCS Directory Node (|UCSPRIMARYDN|) needs to be installed with a unique
  hostname, not used in the AD domain.

* The UCS Directory Node needs to be installed with the same DNS domain name,
  NetBIOS (pre Windows 2000) domain name and Kerberos realm as the AD domain. It
  is also recommended to configure the same LDAP base DN.

* The UCS Directory Node needs to be installed with a unique IPv4 address in
  the same IP subnet as the Active Directory domain controller that is used for
  the takeover.

.. caution::

   If the system is already a member of an Active Directory Domain, installing
   the *Active Directory Takeover* application removes this membership.
   Therefore, the installation of the *Takeover* application has to take place
   only shortly before the actual takeover of the AD domain.

The *Active Directory Takeover* application must be installed from the
Univention App Center for the migration. It must be installed on the system
where the Univention S4 Connector is running (see :ref:`windows-s4-connector`,
usually the |UCSPRIMARYDN|).

.. _windows-ad-takeover-preparations:

Preparation
-----------

The following steps are strongly recommended before attempting the takeover:

* A backup of the AD server(s) should be performed.

* If user logins to the AD server are possible (e.g. through domain logins or
  terminal server sessions) it is recommended to deactivate them and to stop any
  services in the AD domain, which deliver data, e.g. mail servers. This ensures
  that no data is lost in case of a rollback to the original snapshot/backup.

* It is recommended to set the same password for the ``Administrator`` account
  on the AD server as the corresponding account in the UCS domain. In case
  different passwords are used, the password that was set last, will be the one
  that is finally valid after the takeover process (timestamps are compared for
  this).

* In a default installation the ``Administrator`` account of the AD server is
  deactivated. It should be activated in the local user management module.

The activation of the ``Administrator`` account on the AD server is recommended
because this account has all the required privileges to copy the GPO SYSVOL
files. The activation can be achieved by means of the :guilabel:`Active
Directory Users and Computers` module or by running the following two commands:

.. code-block::

   > net user administrator /active:yes
   > net user administrator PASSWORD


.. _windows-ad-takeover-migrate:

Domain migration
----------------

The takeover must be initiated on the UCS Directory Node that runs the
Univention S4 Connector (by default the |UCSPRIMARYDN|). During the takeover
process Samba must only run on this UCS system. If other UCS Samba/AD Nodes are
present in the UCS domain, Samba needs to be stopped on those systems. This is
important to avoid data corruption by mixing directory data taken over from
Active Directory with Samba/AD directory data replicated from other UCS Samba/AD
Nodes.

Other UCS Samba/AD systems can be stopped by logging into each of the other UCS
Directory Nodes as the ``root`` user and running

.. code-block:: console

   $ /etc/init.d/samba4 stop


After ensuring that only the Univention S4 Connector host runs Samba/AD, the
takeover process can be started. If the UCS domain was installed initially with
a UCS version before UCS 3.2, the following |UCSUCRV| needs to be set first:

.. code-block:: console

   $ ucr set connector/s4/mapping/group/grouptype=false

The takeover is performed with the UMC module :guilabel:`Active Directory
Takeover`. The IP address of the AD system must be specified under *Name or
address of the Domain Controller*. An account from the AD domain must be
specified under *Active Directory Administrator account* which is a member of
the AD group ``Domain Admins`` (e.g., the ``Administrator``) and the
corresponding password entered under *Active Directory Administrator password*.

.. _windows-ad-takeover1:

.. figure:: /images/takeover1.*
   :alt: First phase of domain migration

   First phase of domain migration

The module checks whether the AD domain controller can be accessed and
displays the domain data to be migrated.

.. _windows-ad-takeover2:

.. figure:: /images/takeover2.*
   :alt: Overview of the data to be migrated

   Overview of the data to be migrated

When :guilabel:`Next` is clicked, the following steps are
performed automatically:

#. Adjust the system time of the UCS system to the system time of the Active
   Directory domain controller in case the UCS time is behind by more than three
   minutes.

#. Join the UCS Directory Node into the Active Directory domain.

#. Start Samba and the Univention S4 connector to replicate the Active Directory
   objects into the UCS OpenLDAP directory.

#. When "*Well Known*" account and group objects (identified by their special
   RIDs) are synchronized into the UCS OpenLDAP, a listener module running on
   each UCS system sets a |UCSUCR| variable to locally to map the English name
   to the non-English AD name.

   These variables are used to translate the English names used in the UCS
   configuration files to the specific names used in Active Directory. To give
   an example, if ``Domain Admins`` has a different name in the AD, then the
   |UCSUCR| variable :envvar:`groups/default/domainadmins` is set to that
   specific name (likewise for uses, e.g.
   :envvar:`users/default/administrator`).

Additional information is logged to :file:`/var/log/univention/ad-takeover.log`
as well as to
:file:`/var/log/univention/management-console-module-adtakeover.log`.

The UCS Directory Node now contains all users, groups and computers of the
Active Directory domain. In the next step, the SYSVOL share is copied, in which
among other things the group policies are stored.

This phase requires the login to the Active Directory domain controller as the
``Administrator`` (or the equivalent non-English name). There a command needs to
be started to copy the group policy files from the Active Directory SYSVOL share
to the UCS SYSVOL share.

The command to be run in shown in the UMC module. If it has been successfully
run, it must be confirmed with :guilabel:`Next`.

.. _windows-ad-sysvol:

.. figure:: /images/takeover3.*
   :alt: Copying the SYSVOL share

   Copying the SYSVOL share

It may be necessary to install the required :command:`robocopy` tool, which is
part of the Windows Server 2003 Resource Kit Tools. Starting with Windows 2008
the tool is already installed.

.. note::

   The ``/mir`` option of :command:`robocopy` mirrors the specified source
   directory to the destination directory. Please be aware that if you delete
   data in the source directory and execute this command a second time, this
   data will also be deleted in the destination directory.

After successful completion of this step, it is now necessary to shutdown all
domain controllers of the Active Directory domain. Then :guilabel:`Next` must be
clicked in the UMC module.

.. _windows-ad-shutdown:

.. figure:: /images/takeover4.*
   :alt: Shutdown of the AD server(s)

   Shutdown of the AD server(s)

The following steps are now automatically performed:

#. Claiming all FSMO roles for the UCS Directory Node. These describe different
   tasks that a server can take on in an AD domain.

#. Register the name of the Active Directory domain controller as a DNS alias
   (see :ref:`ip-config-cname-record-alias-records`) for the UCS DNS server.

#. Configure the IP address of the Active Directory domain controller as a
   virtual Ethernet interface.

#. Perform some cleanup, e.g. removal of the AD domain controller account and
   related objects in the Samba SAM account database.

#. Finally restart Samba and the DNS server.

.. _windows-ad-takeover-finalsteps:

Final steps of the takeover
---------------------------

Finally the following steps are required:

#. The domain function level of the migrated Active Directory domain needs to be
   checked by running the following command:

   .. code-block:: console

      > samba-tool domain level show


   In case this command returns the message ``ATTENTION: You
   run SAMBA 4 on a forest function level lower than Windows 2000
   (Native).`` the following commands should be run to fix this:

   .. code-block:: console

      > samba-tool domain level raise --forest-level=2003 --domain-level=2003
      > samba-tool dbcheck --fix --yes

#. In case there has been more than one Active Directory domain controller in
   the original Active Directory domain, all the host accounts of the other
   domain controllers must be removed in the computers management UMC modules.
   In addition their accounts must be removed from the Samba SAM database. This
   may be done by logging in to a migrated Windows client as member of the group
   ``Domain Admins`` and running the tool :program:`Active Directory Users and
   Computers`.

#. If more than one UCS Directory Node with Samba/AD has been installed,
   these servers need to be re-joined.

#. All Windows clients need to be rebooted.

.. _windows-ad-takeover-tests:

Tests
-----

It is recommended to perform thorough tests with Windows client systems,
e.g.

* Login to a migrated client as a migrated user.

* Login to a migrated client as the *Administrator*.

* Test group policies.

* Join of a new Windows client.

* Create a new UCS user and login to a Windows client.
