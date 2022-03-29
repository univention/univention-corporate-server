.. _windows-addomain:

Operation of a Samba domain based on Active Directory
=====================================================

.. _windows-setup4:

Installation
------------

Samba as an AD domain controller can be installed on all UCS Directory Nodes
from the Univention App Center with the application *Active Directory-compatible
domain controller*. Alternatively, the software package
:program:`univention-samba4` can be installed. On the system roles
|UCSPRIMARYDN| and |UCSBACKUPDN| the :program:`univention-s4-connector` package
must also be installed and :command:`univention-run-join-scripts` command must
be run after installation. Additional information can be found in
:ref:`computers-softwaremanagement-installsoftware`.

A Samba member server can be installed on UCS Managed Nodes from the Univention
App Center with the application :program:`Windows-compatible Fileserver`.
Alternatively, the software package :program:`univention-samba` can be installed
(:command:`univention-run-join-scripts` command must be run after installation).
Additional information can be found in
:ref:`computers-softwaremanagement-installsoftware`.

Samba supports the operation as a *read-only domain controller*. The setup is
documented in `Extended Windows integration documentation
<https://docs.software-univention.de/windows-5.0.html>`_.

.. _windows-samba4-services:

Services of a Samba domain
--------------------------

.. _windows-samba4-services-auth:

Authentication services
^^^^^^^^^^^^^^^^^^^^^^^

User logins can only be performed on Microsoft Windows systems joined in the
Samba domain. Domain joins are documented in :ref:`windows-domain-join`.

Users who login to a Windows system are supplied with a Kerberos ticket when
they login. The ticket is then used for the further authentication. This ticket
allows access to the domain's resources.

Common sources of error in failed logins are:

* Synchronization of the system times between the Windows client and domain
  controller is essential for functioning Kerberos authentication. By default
  the system time is updated via NTP during system startup. This can also be
  done manually using the command :command:`w32tm /resync` on the Windows
  client.

* DNS service records need to be resolved during login. For this reason, the
  Windows client should use the domain controller's IP address as its DNS name
  server.

.. _windows-samba4-fileservices:

File services
^^^^^^^^^^^^^

A file server provides files over the network and allows concentrating the
storage of user data on a central server.

The file services integrated in UCS support the provision of shares using the
CIFS protocol (see :ref:`shares-general`). Insofar as the underlying file system
supports Access Control Lists (ACLs) (can be used with ``ext4`` and ``XFS``),
the ACLs can also be used by Windows clients.

Samba Active Directory domain controllers, i.e. UCS Directory Nodes, can also
provide file services. As a general rule, it is recommended to separate domain
controllers and file/print services in Samba environments - following the
Microsoft recommendations for Active Directory - that means using UCS Directory
Nodes for logins/authentication and UCS Managed Nodes for file/print services.
This ensures that a high system load on a file server does not result in
disruptions to the authentication service. For smaller environments in which it
is not possible to run two servers, file and print services can also be run on a
UCS Directory Node.

Samba supports the *CIFS* protocol and the successor *SMB2* to provide file
services. Using a client which supports *SMB2* (as of :program:`Windows Vista`,
i.e., :program:`Windows 7/8` too) improves the performance and scalability.

The protocol can be configured using the |UCSUCR| variable
:envvar:`samba/max/protocol`. It must be set on all Samba servers and then all
Samba server(s) restarted.

* ``NT1`` configures *CIFS* (supported by all Windows versions)

* ``SMB2`` *SMB2* (supported as of :program:`Windows Vista` / :program:`Windows 7`)

* ``SMB3`` configures *SMB3* (supported as of :program:`Windows 8`)

.. _windows-samba4-services-print:

Print services
^^^^^^^^^^^^^^

Samba offers the possibility of sharing printers set up under Linux as network
printers for Windows clients. The management of the printer shares and the
provision of the printer drivers is described in :ref:`print-general`.

Samba AD domain controllers can also provide print services. In this case, the
restrictions described in :ref:`windows-samba4-fileservices` must be taken into
consideration.

.. _windows-s4-connector:

Univention S4 connector
^^^^^^^^^^^^^^^^^^^^^^^

When using Samba as an Active Directory domain controller, Samba provides a
separate LDAP directory service. The synchronization between the UCS LDAP and
the Samba LDAP occurs via an internal system service, the *Univention S4
connector*. The connector is enabled on the |UCSPRIMARYDN| by default and
typically requires no further configuration.

Further information on the status of the synchronization can be found in
the log file
:file:`/var/log/univention/connector-s4.log`. Additional
information on analyzing connector replication problems can be found in
:uv:kb:`Samba 4 Troubleshooting <32>`.

The :command:`univention-s4search` command can be used to
search in the Samba directory service. If it is run as the
``root`` user, the required
credentials of the machine account are used automatically:

.. code-block:: console

   $ root@primary:~# univention-s4search sAMAccountName=Administrator
   # record 1
   dn: CN=Administrator,CN=Users,DC=example,DC=com
   objectClass: top
   objectClass: person
   objectClass: organizationalPerson
   objectClass: user
   cn: Administrator
   instanceType: 4
   (..)


.. _windows-multimaster:

Replication of directory data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Samba/AD domains use the Directory Replication System (DRS) to replicate
the directory data. DRS allows multi-master replication, i.e., the write
changes from multiple domain controllers are synchronized at protocol
level. Consequently, the use of snapshots in virtualization solutions
should be avoided when using Samba/AD and Samba/AD should be operated on
a server which is never switched off.

The complexity of the multi-master replication increases with each
additional Samba/AD domain controller. Consequently, it must be checked
whether additional Samba/AD domain controllers provided by UCS Directory
Nodes are necessary or if a UCS Managed Node would not be a better
choice for new servers.

Additional information on troubleshooting replication problems can be
found in :uv:kb:`Samba 4 Troubleshooting <32>`.

.. _windows-sysvolshare:

Synchronization of the SYSVOL share
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The SYSVOL share is a share which provides group policies and logon scripts in
Active Directory/Samba. It is synchronized among all domain controllers and
stored in the :file:`/var/lib/samba/sysvol/` directory.

In Microsoft Active Directory, the SYSVOL share is synchronized by the File
Replication Service (introduced with :program:`Windows 2000`) or the Distributed
File System (as of :program:`Windows 2008 R2`). These replication methods are
not yet fully implemented in Samba/AD. The synchronization between the Samba/AD
domain controllers is performed in UCS via a Cron job (every five minutes as
standard - can be configured using the |UCSUCRV|
:envvar:`samba4/sysvol/sync/cron`).

.. _windows-samba4-desktopmanagement:

Configuration and management of Windows desktops
------------------------------------------------

.. _gruppenrichtlinien:

Group policies
^^^^^^^^^^^^^^

Group policies are an Active Directory feature which allows the central
configuration of settings for computers and users. Group policies are also
supported by Samba/AD domains. The policies only apply to Windows clients; Linux
or Mac OS systems cannot evaluate the policies.

Group policies are often referred to as GPOs (*group policy objects*). Put more
precisely, a GPO can contain a series of policies. Despite their name, group
policy objects cannot be assigned directly to certain user groups, but instead
are linked with certain AD administration units (domains, sites or
organizational units) in the Samba directory service (Samba AD/DS) and thus
refer to subordinate objects. A group-specific or user-specific evaluation is
only indirectly possible via the *Security Filtering* of a group policy object,
in which the *Apply group policy Allow/Deny* privilege can be directly
restricted to certain groups, users or computers.

As a basic rule, a distinction must be made between *group policies* (GPOs) and
the similarly named *group policy preferences (GPPs)*:

* The settings made via *GPOs* are binding, whereas *GPPs* are merely used to
  enter preferences in the registry of Windows clients, which can still be
  overwritten on the client in certain circumstances.

* The settings made via *GPOs* are also dynamically applied to the target
  objects, whereas, in contrast, the settings made via *GPPs* are entered
  statically in the registry of Windows clients (this is also referred to as
  *tattooing*).

For these reasons, *GPOs* are preferable to *GPPs* in the majority of cases.
This remainder of this section deals exclusively with *GPOs*.

In contrast to UCS policies (see :ref:`central-policies`), group policies are
not configured via UMC modules, but instead are configured in a separate editor,
the *Group Policy Management* editor, which is a component of the *Remote Server
Administration Tools (RSAT)*. The installation is described in
:ref:`gpo-install`.

There are two types of policies:

User policies
   *User policies* configure a user's settings, e.g., the configuration of the
   desktop. It is also possible to configure applications via group policies
   (e.g., the start page of a browser or settings in LibreOffice).

Computer policies
   *Computer policies* define a Windows client's settings.

Computer policies are evaluated for the first time the computer starts
up; user policies during login. The policies are also continually
evaluated for logged in users / running systems and updated (every
90-120 minutes by default. The period varies at random to avoid peak
loads.)

The command :command:`gpupdate /force` can also be run
specifically to start the evaluation of group policies.

Some policies - e.g., for the installation of software or for login
scripts - are only evaluated during login (user policies) or system
startup (computer policies).

The majority of group policies only set one value in the Windows
registry, which is then evaluated by Windows or an application. As
standard users cannot modify any settings in the corresponding section
of the Windows registry, it is also possible to configure restricted
user desktops in which, for example, users cannot open the Windows Task
Manager.

The group policies are stored in the SYSVOL share, see :ref:`windows-sysvolshare`. They are linked with user
and host accounts in the Samba directory service.

.. _gpo-install:

Installation of Group Policy Management
'''''''''''''''''''''''''''''''''''''''

:program:`Group Policy Management` can be installed as a component of the
*Remote Server Administration Tools* on Windows clients. They can be found at
`Remote Server Administration Tools (RSAT) for Windows 10
<https://www.microsoft.com/en-us/download/details.aspx?id=45520>`_.

.. _windows-gpo-activate:

.. figure:: /images/gpo-activate.*
   :alt: Activating the Group Policy Management tools

   Activating the Group Policy Management tools

Following the installation, Group Policy Management must still be enabled in the
Windows Control Panel. This is done by enabling the *Group Policy Management
Tools* option under :menuselection:`Start --> Control Panel --> Programs -->
Turn Windows features on or off --> Remote Server Administration Tools -->
Feature Administration Tools`.

Following the enabling, Group Policy Management can be run under
:menuselection:`Start --> Administrative Tools --> Group Policy Management`.

.. _gpo-config:

Configuration of policies with Group Policy Management
''''''''''''''''''''''''''''''''''''''''''''''''''''''

Group policies can only be configured by users who are members of the ``Domain
Admins`` group (e.g., the ``Administrator``). When logging in, attention must be
paid to logging in with the domain Administrator account and not the local
Administrator account. Group Policy Management can be run on any system in the
domain.

If more than one Samba domain controller is in use, consideration must be given
to the replication of the GPO data, see :ref:`gpo-gposync`.

There are two basic possibilities for creating GPOs:

* They can be created in the *Group Policy Objects* folder and then linked to
  different positions in the LDAP. This is practical if a policy is to be linked
  to several positions in the LDAP.

* The GPO can also be created at an LDAP position ad hoc and then directly
  linked to it. This is the simpler means for small and medium*sized domains.
  Domains created ad hoc are also shown in the *Group Policy Objects* folder.

A policy can have one of three statuses: ``enabled``, ``disabled`` or ``unset``.
The effect is always based on the formulation of the policy. For example, if it
says *Disable feature xy*, the policy must be enabled to switch off the feature.
Some policies have additional options, for example the *Enable mail quota*
policy could include an additional option for managing the storage space.

.. _windows-gpo-edit:

.. figure:: /images/gpo-edit-policy.*
   :alt: Editing a policy

   Editing a policy

Two standard policy objects are predefined:

Default Domain Policy
   The *Default Domain Policy* object can be used to configure global policies
   for all users and computers within the same domain.

Default Domain Controllers Policy
   The *Default Domain Controllers Policy* object has no use in a Samba domain
   (in a Microsoft AD domain the policies for Microsoft domain controllers would
   be performed via this object). The configuration of the Samba domain
   controllers in UCS is largely performed via |UCSUCR|.

AD domains can be structured in sites. All the sites are listed in the
main menu of *Global Policy Management*. There is also a list of the
domains there. The current Samba versions do not support forest domains,
so there is only ever one domain displayed here.

One domain can be structured in different organizational units (OUs).
This can, for example, be used to store the employees from accounting
and the users in the administration department in different LDAP
positions.

Group policies can mutually overlap. In this case, the inheritance principle
applies, e.g., the superordinate policies overwrite the subordinate ones. The
applicable policies for a user can be displayed on the Windows client either
with the modeling wizard in *Group Policy Management* or by entering the command
:command:`gpresult /user USERNAME /v` in the Windows command line.

.. _windows-gpo-user:

.. figure:: /images/gpo-gpresult.*
   :alt: Evaluating the GPO for the user ``user01``

   Evaluating the GPO for the user ``user01``

The policies are evaluated in the following order:

* By default *Default Domain Policy* settings apply for all the users and
  computers within the domain.

* Policies linked to an OU overwrite policies from the default domain policy.
  If the OUs are nested further, in the case of conflict, the "most subordinate"
  policies in each case, in other words the one most closely linked to the
  target object, apply. The following evaluation order applies:

  * Assignment of a policy to an Active Directory site

  * Settings of the default domain policy

  * Assignment of a policy to an organizational unit (OU) (in turn, each
    subordinate OU overrules policies from superordinate OUs).

Example: A company blocks access to the :program:`Windows Task Manager` in general.
This is done by enabling the :guilabel:`Remove Task Manager`
policy in the *Default Domain Policy* object.
However, the Task Manager should still be available to some staff with
the requisite technical expertise. These users are saved in the
*IT staff* OU. An additional group policy object
is now created in which the :guilabel:`Remove Task Manager`
policy is set to *disabled*. The new GPO is linked
with the *IT staff* OU.

.. _gpo-gposync:

Configuration of group policies in environments with more than one Samba domain controller
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

A group policy is technically composed of two parts: On the one hand there is a
directory in the domain controllers' file system which contains the actual
policy files which are to be implemented on the Window system (saved in the
SYSVOL share (see :ref:`windows-sysvolshare`)). On the other hand there is an
object with the same name in the LDAP tree of the Samba directory service (Samba
AD/DS), which is usually saved below an LDAP container named *Group Policy
Objects*.

Although the LDAP replication between the domain controllers is performed in
just a few seconds, the files in the SYSVOL share are only replicated every five
minutes in the default setting. It must be noted that the application of newly
configured group policies in this period may fail if a client happens to consult
a domain controller which has not yet replicated the current files.

.. _gpo-adm:

Administrative templates (ADMX/ADM)
'''''''''''''''''''''''''''''''''''

The policies displayed in *Group Policy Management* can be expanded with
so-called *administrative templates*. This type of template defines the name
under which the policy should appear in Group Policy Management and which value
should be set in the Windows registry. Administrative templates are saved in
so-called *ADMX files* (previously *ADM files*), see `Group Policy ADMX Syntax
Reference Guide
<https://docs.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2008-R2-and-2008/cc753471(v=ws.10)?redirectedfrom=MSDN>`_.

Among other things, ADMX files offer the advantage that they can be provided
centrally across several domain controllers so that Group Policy Management on
all Windows clients displays the same configuration possibilities, see `How to
Implement the Central Store for Group Policy Admin Templates, Completely (Hint:
Remove Those .ADM files!)
<https://techcommunity.microsoft.com/t5/core-infrastructure-and-security/how-to-implement-the-central-store-for-group-policy-admin/ba-p/255448>`_.

The following example of an ADM file defines a computer policy in which a
registry key is configured for the (fictitious) Univention RDP client. ADM files
can also be converted to the newer ADMX format using third-party tools. Further
information on the format of ADM files can be found at `Writing Custom ADM
Files for System Policy Editor <https://support.microsoft.com/en-us/kb/225087>`_
and `How to create custom ADM templates
<http://www.frickelsoft.net/blog/downloads/howto_admTemplates.pdf>`_.  The
administrative template must have the file suffix :file:`.adm`:

.. code-block::

   CLASS MACHINE
   CATEGORY "Univention"
   POLICY "RDP client"
   KEYNAME "Univention\RDP\StorageRedirect"
   EXPLAIN "If this option it activated, sound output is enabled in the RDP client"
   VALUENAME "Sound redirection"
   VALUEON "Activated"
   VALUEOFF "Deactivated"
   END POLICY
   END CATEGORY


.. _windows-gpo-admin:

.. figure:: /images/gpo-adm-template.*
   :alt: The activated administrative template

   The activated administrative template

The ADM file can then be converted to the ADMX format or imported directly via
Group Policy Management. This is done by following the context menu
:menuselection:`Administrative templates --> Add/Remove Templates` option.
:guilabel:`Add` can be used to import an ADM file. The administrative templates
are also saved in the SYSVOL share and replicated, which allows Group Policy
Management to access them from the Windows clients.

.. _gpo-wmifilter:

Application of policies based on computer properties (WMI filters)
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

It is also possible to configure policies based on system properties. These
properties are provided via the Windows Management Instrumentation interface.
The mechanism which builds on this is known as *WMI filtering*. This makes it
possible, for example, to apply a policy only to PCs with a 64-bit processor
architecture or with at least 8 GB of RAM. If a system property changes (e.g.,
if more memory is installed), the respective filter is automatically
re-evaluated by the client.

The WMI filters are displayed in the domain structure in the *WMI Filters*
container. :guilabel:`New` can be used to define an additional filter. The
filter rules are defined under *Queries*. The rules are defined in a syntax
similar to SQL. Examples rules can be found in `WMI filtering using GPMC
<https://www.microsoft.com/en-US/download/details.aspx?id=53314>`_  and `Filtern
von Gruppenrichtlinien anhand von Benutzergruppen, WMI und
Zielgruppenadressierung (German)
<https://www.gruppenrichtlinien.de/artikel/filtern-von-gruppenrichtlinien-anhand-von-benutzergruppen-wmi-und-zielgruppenadressierung/>`_.

.. _netlogon-freigabe-samba4:

Logon scripts / NETLOGON share
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The NETLOGON share serves the purpose of providing logon scripts in Windows
domains. The logon scripts are executed following after the user login and allow
the adaptation of the user's working environment. Scripts have to be saved in a
format which can be executed by Windows, such as :file:`bat`.

The logon scripts are stored in
:samp:`/var/lib/samba/sysvol/{Domainname}/scripts/` and provided under the share
name *NETLOGON*. The file name of the script must be given relative to that
directory.

The NETLOGON share is replicated within the scope of the SYSVOL replication.

The logon script can be assigned for each user, see :ref:`users-management`.

.. _windows-serverhome-samba4:

Configuration of the file server for the home directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The home directory can be defined user-specifically in the UMC module
:guilabel:`Users`, see :ref:`users-management`. This is performed with the
setting *`Windows home path*, e.g., :literal:`\\\\ucs-file-server\smith`.

The multi edit mode of UMC modules can be used to assign the home directory to
multiple users at one time, see :ref:`central-user-interface-edit`.

.. _windows-roamingprofiles-samba4:

Roaming profiles
^^^^^^^^^^^^^^^^

Samba supports roaming profiles, i.e., user settings are saved on a
central server. This directory is also used for storing the files which
the user saves in the *My Documents* folder.
Initially, these files are stored locally on the Windows computer and
then synchronized onto the Samba server when the user logs off.

No roaming profiles are used by default in Samba/AD.

Roaming profiles can be configured via a group policy found under
:menuselection:`Computer configuration --> Policies --> Administrative templates
--> System --> User profiles --> Set roaming profile path for all users logging
onto this computer`. If this is set to the UNC path
:file:`%LOGONSERVER%\\%USERNAME%\\windows-profiles\\default` the profile data will
get written to the directories :samp:`windows-profiles\\default.V{?}` in the home
directory of the user located on the currently chosen logon server.

Alternatively the profile path can be defined for individual user accounts. This
is possible in the UMC module :guilabel:`Users` under the *Account* tab by
filling the field *Windows profile directory*. The corresponding UDM property is
called ``profilepath``. In the OpenLDAP backend this is stored in the LDAP
attribute ``sambaProfilePath``.

If the profile path is changed, then a new profile directory will be
created. The data in the old profile directory will be kept. These data
can be manually copied or moved to the new profile directory. Finally,
the old profile directory can be deleted.

.. note::

   As standard, the ``Administrator`` accesses shares with ``root`` rights. If
   as a result the profile directory is created with the root user, it should be
   manually assigned to the ``Administrator`` with the command :command:`chown`.
