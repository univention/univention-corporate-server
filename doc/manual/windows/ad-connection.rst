.. _ad-connector-general:

Active Directory Connection
===========================

|UCSUCS| can be operated together with an existing Active Directory domain (AD
domain) in two different ways. Both modes can be set up using the
:program:`Active Directory Connection` application from the Univention App
Center (see :ref:`computers-softwaremanagement-installsoftware`). This is
available on a |UCSPRIMARYDN| and |UCSBACKUPDN|.

The two modes are:

* UCS as a part (domain member) of an AD domain (see
  :ref:`ad-connector-ad-member-setup`)

* Synchronization of account data between an AD domain and a UCS domain (see
  :ref:`ad-connector-ad-connector-setup`).

In both modes, the :program:`Active Directory Connection` service is used in UCS
(UCS AD Connector for short), which can synchronize the directory service
objects between a Windows 2012/2016/2019 server with Active Directory (AD) and
the OpenLDAP directory of |UCSUCS|.

In the first case, the configuration of a UCS server system as a member of an AD
domain, the AD functions as the primary directory service and the respective UCS
system joins the trust context of the AD domain. The domain membership gives the
UCS system restricted access to the account data of the Active Directory domain.
The setup of this operating mode is described in detail in
:ref:`ad-connector-ad-member-setup`.

The second mode, which can be configured via the :program:`Active Directory Connection`
app, is used to run the UCS domain parallel to an existing AD domain. In this
mode, each domain user is assigned a user account with the same name in both the
UCS and the AD domain. Thanks to the use of the name identity and the
synchronization of the encrypted password data, this mode allows transparent
access between the two domains. In this mode, the authentication of a user in
the UCS domain occurs directly within the UCS domain and as such is not directly
dependent on the AD domain. The setup of this operating mode is described in
detail in :ref:`ad-connector-ad-connector-setup`.

.. _ad-connector-ad-member-setup:

UCS as a member of an Active Directory domain
---------------------------------------------

In the configuration of a UCS server system as a member of an AD domain (*AD
member* mode), the AD functions as the primary directory service and the
respective UCS system joins the trust context of the AD domain. The UCS system
is not able to operate as an Active Directory domain controller itself. The
domain membership gives the UCS system restricted access to the account data of
the Active Directory domain, which it exports from the AD by means of the UCS AD
Connector and writes locally in its own OpenLDAP-based directory service. In
this configuration, the UCS AD Connector does not write any changes in the AD.

The *AD member* mode is ideal for expanding an AD domain with applications that
are available on the UCS platform. Apps installed on the UCS platform can then
be used by the users of the AD domain. The authentication is still performed
against native Microsoft AD domain controllers.

The setup wizard can be started directly from the UCS installation by selecting
*Join into an existing Active Directory domain*. Subsequently, the setup wizard
can be installed with the app *Active Directory Connection* from the Univention
App Center. Alternatively, the software package
:program:`univention-ad-connector` can be installed. Further information can be
found in :ref:`computers-softwaremanagement-installsoftware`.

.. note::

   * The *AD member* mode can only be configured on a |UCSPRIMARYDN|.

   * The name of the DNS domain of the UCS systems must match that of the AD
     domain. The hostname must of course be different.

   * All the AD and UCS servers in a connector environment must use the same
     time zone.

.. _windows-gpo-mode:

.. figure:: /images/admember_1.*
   :alt: Configuration of the operating mode as part of an AD domain

   Configuration of the operating mode as part of an AD domain

In the first dialogue window of the setup wizard, the point *Configure UCS as
part of an AD domain* is preselected and can be confirmed with :guilabel:`Next`.

The next dialogue window requests the address of an AD domain controller as well
as the name of the standard administrator account of the AD domain and its
password. The standard AD administrator account should be used here. The
specified AD domain controller should also provide DNS services for the domain.
Pressing the :guilabel:`Join AD domain` button starts the domain join.

.. _windows-ad-join:

.. figure:: /images/admember_2.*
   :alt: Domain join of an AD domain

   Domain join of an AD domain

If the system time of the UCS system is more than 5 minutes ahead of the
system time of the AD domain controller, manual adjustment of the system
times is required. This is necessary because the AD Kerberos
infrastructure is used for the authentication. System times should not,
however, be turned back, in order to avoid inconsistencies.

The domain join is performed automatically. The subsequent dialogue window
should be confirmed with :guilabel:`Finish`. Then the UMC server should be
restarted by clicking :guilabel:`Restart`.

.. note::

   Once the *AD member* mode has been set up, the authentication is performed
   against the AD domain controller. **Consequently, the password from the AD
   domain now applies for the administrator.** If an AD domain with a non-English
   language convention has been joined, the ``administrator`` account from UCS
   is automatically changed to the spelling of the AD during the domain join.
   The same applies for all user and group objects with *Well Known SID* (e.g.,
   ``Domain Admins``).

.. warning::

   If additional UCS systems were already part of the UCS domain in
   addition to the |UCSPRIMARYDN|, they must also join the domain anew. At
   the same time they recognize that the |UCSPRIMARYDN| is in
   *AD member* mode and also join the
   authentication structure of the AD domain and can then also provide
   Samba file shares, for example.

.. note::

   As the AD Kerberos infrastructure is used for the authentication of
   users in this mode, it is essential that the system times of UCS and
   the AD domain controller are synchronized (with a tolerance of 5
   minutes). For this purpose, the AD domain controller is configured as
   the NTP time server in UCS. In the case of authentication problems,
   the system time should always be the first thing to be checked.

Following this setup, the UMC module :guilabel:`Active Directory Connection` can
be used for further administration, e.g., for checking whether the service is
running and to restart it if necessary (see :ref:`ad-connector-restart`).

To use an encrypted connection between Active Directory and the |UCSPRIMARYDN|
not only for the authentication, but also for data exchange itself, the root
certificate of the certification authority can be exported from the AD domain
controller and uploaded via the UMC module. Further information on this topic
is available in :ref:`ad-connector-ad-certificate`.

By default the Active Directory connection setup in this way does not transfer
any password data from AD to the UCS directory service. Some apps from the
Univention App Center require encrypted password data. If an app needs it, a
note is shown in the App Center.

In *AD member* mode the UCS AD Connector exports object data from the AD with
the authorizations of the |UCSPRIMARYDN|'s machine account by default. These
authorizations are not sufficient for exporting encrypted password data. In this
case, the LDAP DN of a privileged replication user can be adjusted manually in
the |UCSUCRV| :envvar:`connector/ad/ldap/binddn`. This must be a member of the
``Domain Admins`` group in the AD. The corresponding password must be saved in a
file on the |UCSPRIMARYDN| and the filename entered in the |UCSUCRV|
:envvar:`connector/ad/ldap/bindpw`. If the access password is changed at a later
point in time, the new password must be entered in this file. The access rights
for the file should be restricted so that only the ``root`` owner has access.

The following commands demonstrate the steps in an example:

.. code-block:: console

   $ ucr set connector/ad/ldap/binddn=Administrator
   $ ucr set connector/ad/ldap/bindpw=/etc/univention/connector/password
   $ touch /etc/univention/connector/password
   $ chmod 600 /etc/univention/connector/password
   $ echo -n "Administrator password" > /etc/univention/connector/password
   $ ucr set connector/ad/mapping/user/password/kinit=false


If needed, the AD domain controller can also be replaced by the
|UCSPRIMARYDN| at a later point in time. This is possible via the
:program:`Active Directory Takeover` application (see
:ref:`windows-adtakeover`).

.. _ad-connector-ad-connector-setup:

Setup of the UCS AD connector
-----------------------------

As an alternative to membership in an AD domain, as described in the previous
section, the :program:`Active Directory Connection` can be used to synchronize
user and group objects between a UCS domain and an AD domain. In addition to
unidirectional synchronization, this operating mode also allows bidirectional
synchronization. In this operating mode, both domains exist in parallel and
their authentication systems function independently. The prerequisite for this
is the synchronization of the encrypted password data.

By default containers, organizational units, users, groups and computers are
synchronized.

The UCS AD connector can only be installed on a |UCSPRIMARYDN| or |UCSBACKUPDN|
system.

Information on the attributes configured in the basic setting and
particularities to take into account can be found in
:ref:`ad-connector-details-on-preconfigured-synchronization`.

The identical user settings in both domains allow users to access services in
both environments transparently. After logging in to a UCS domain, subsequent
connection to a file share or to an Exchange server with Active Directory is
possible without a renewed password request. Users and administrators will find
users and groups of the same name on the resources of the other domain and can
thus work with their familiar permission structures.

The initialization is performed after the first start of the connector. All the
entries are read out of the UCS, converted to AD objects according to the
mapping set and added (or modified if already present) on the AD side. All the
objects are then exported from the AD and converted to UCS objects and
added/modified accordingly on the UCS side. As long as there are changes, the
directory service servers continue to be requested. The UCS AD connector can
also be operated in a unidirectional mode.

Following the initial sync, additional changes are requested at a set interval.
This value is set to five seconds and can be adjusted manually using the
|UCSUCR| variable :envvar:`connector/ad/poll/sleep`.

If an object cannot be synchronized, it is firstly reset (“rejected”).
Following a configurable number of cycles – the interval can be adjusted using
the |UCSUCR| variable :envvar:`connector/ad/retryrejected` – another attempt is
made to import the changes. The standard value is ten cycles. In addition, when
the UCS AD Connector is restarted, an attempt is also made to synchronize the
previously rejected changes again.

.. _ad-connector-basicsetup:

Basic configuration of the UCS AD Connector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The UCS AD Connector is configured using a wizard in the UMC module
:guilabel:`Active Directory Connection`.

The module can be installed from the Univention App Center with the application
:program:`Active Directory Connection`. Alternatively, the software package
:program:`univention-ad-connector` can be installed. Additional information can
be found in :ref:`computers-softwaremanagement-installsoftware`.

.. note::

   All AD and UCS servers in a connector environment must use the same time
   zone.

.. warning::

   Despite intensive tests it is not possible to rule out that the results of
   the synchronization may affect the operation of a productive domain. The
   connector should therefore be tested for the respective requirements in a
   separate environment in advance.

It is convenient to perform the following steps with a web browser from the AD
domain controller, as the files need to be downloaded from the AD domain
controller and uploaded to the wizard.

In the first dialog window of the setup wizard, the point *Synchronization of
content data between an AD and this UCS domain* must be selected and confirmed
with :guilabel:`Next`.

.. _windows-ad-connector:

.. figure:: /images/adconnector_1.*
   :alt: Configuration of the UCS AD Connector via UMC module

   Configuration of the UCS AD Connector via UMC module

The address of an AD domain controller is requested in the next dialogue window.
Here you can specify the IP address of a fully qualified DNS name. If the UCS
system is not be able to resolve the computer name of the AD system, the AD DNS
server can either be configured as the DNS forwarder under UCS or a DNS host
record can be created for the AD system in the UMC module :guilabel:`DNS` (see
:ref:`networks-dns-hostrecord`).

Alternatively, a static entry can also be adopted in :file:`/etc/hosts` via
|UCSUCR|, e.g.

.. code-block:: console

   $ ucr set hosts/static/192.0.2.100=w2k8-32.ad.example.com

In the *Active Directory account* field, the user is configured which is used
for the access on the AD. The setting is saved in the |UCSUCRV|
:envvar:`connector/ad/ldap/binddn`. The replication user must be a member of the
``Domain Admins`` group in the AD.

The password used for the access must be entered in the *Active Directory
password* field. On the UCS system it is only saved locally in a file which only
the ``root`` user can read.

:ref:`ad-connector-ad-password` describes the steps required if these access
data need to be adjusted at a later point in time.

Clicking on :guilabel:`Next` prompts the setup wizard to check the connection
to the AD domain controller. If it is not possible to create an
SSL/TLS-encrypted connection, a warning is emitted in which you are advised to
install a certification authority on the AD domain controller. It is recommended
to follow this advice.

UCS 5.0 requires TLS 1.2, which needs to be activated manually for Windows
Server Releases prior to 2012R2. UCS 5.0 doesn't support the hash algorithm
SHA-1 any longer. If this has been used in the creation of the AD root
certificate or for the certificate of the Windows server then they should be
replaced.

Following this step, the setup can be continued by clicking :guilabel:`Next`
again. If it is still not possible to create an SSL/TLS-encrypted connection, a
security query appears asking whether to set up the synchronization without SSL
encryption. If this is needed, the setup can be continued by clicking
:guilabel:`Continue without encryption`. In this case, the synchronization of
the directory data is performed unencrypted.

If the AD domain controller supports SSL/TLS-encrypted connections, the setup
wizard offers :guilabel:`Upload AD root certificate` in the next step. This
certificate must be exported from the AD certification authority in advance (see
:ref:`ad-connector-ad-certificate`). In contrast, if this step is skipped, the
certificate can also be uploaded via the UMC module at a later point in time and
the SSL/TLS encryption enabled (until that point all directory data will,
however, be synchronized unencrypted).

The connector can be operated in different modes, which can be selected in the
next dialogue window *Configuration of Active Directory domain synchronization*.
In addition to bidirectional synchronization, replication can also be performed
in one direction from AD to UCS or from UCS to AD. Once the mode has been
selected, :guilabel:`Next` needs to be clicked.

Once :guilabel:`Next` is clicked, the configuration is taken over and the UCS AD
Connector started. The subsequent dialogue window needs to be closed by clicking
on :guilabel:`Finish`.

Following this setup, the UMC module :guilabel:`Active Directory Connection`
can be used for further administration of the Active Directory Connection, e.g.,
for checking whether the service is running and restart it if necessary (see
:ref:`ad-connector-restart`).

.. note::

   The connector can also synchronize several AD domains within one UCS domain;
   this is documented in `Extended Windows integration documentation
   <https://docs.software-univention.de/windows-5.0.html>`_.

.. _windows-ad-dialog:

.. figure:: /images/adconnector_2.*
   :alt: Administration dialogue for the Active Directory Connection

   Administration dialogue for the Active Directory Connection

.. _ad-connector-ad-certificate:

Importing the SSL certificate of the Active Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A SSL certificate must be created on the Active Directory system and the root
certificate exported to allow encrypted communication. The certificate is
created by the Active Directory's certificate service. The necessary steps
depend on the Windows versions used. Three versions are shown below as examples.

The encrypted communication between the UCS system and Active Directory can also
be deactivated by setting the |UCSUCRV| :envvar:`connector/ad/ldap/ssl` to
``no``. This setting does not affect the replication of encrypted password
data.

.. _windows-adconn-win2012:

Exporting the certificate on Windows 2012 / 2016 / 2019
"""""""""""""""""""""""""""""""""""""""""""""""""""""""

If the certificate service is not installed, it must be installed before
proceeding.

The server manager must be opened. There, select the *Active Directory
Certificate Services* role in the :menuselection:`Manage --> Add Roles and
Features` menu. When selecting the role services, it is sufficient simply to
select *Certification Authority*. A yellow warning triangle is then shown in the
top bar in the server manager. Here, the :guilabel:`Configure Active Directory
Certificate Services on the server` option must be selected. *Certification
Authority* is selected as the role service to be configured. The type of
installation is :menuselection:`Enterprise CA --> Root CA` Now, click on
:guilabel:`Create a new private key` and confirm the suggested encryption
settings and the suggested name of the certification authority. Any period of
validity can be set. The standard paths can be used for the database location.

The AD server must then be restarted.

This certificate must now be exported and copied onto the UCS system:
:menuselection:`Server Manager --> Active Directory Certificate Services`. Then
right click on the server and select :guilabel:`Certification Authority`. There,
right click on the name of the generated certificate and :menuselection:`Open
--> Copy to File --> DER encoded binary X.509 (.CER) --> Select an arbitrary
filename --> Finish`.

A computer list is shown there and the elements *Revoked Certificates*, *Issued
Certificates*, *Pending Requests*, *Failed Requests* and *Certificate Templates*
displayed under every system. Here, one must right click on the computer name -
not on one of the elements - and then select :guilabel:`Properties`. The root
certificate is usually called ``Certificate #0``. Then select
:menuselection:`Open --> Copy to File --> DER encoded binary X.509 (.CER) -->
Select an arbitrary filename --> Finish`.

.. _windows-copying-the-active-directory-certificate-to-the-ucs-system:

Copying the Active Directory certificate to the UCS system
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

The SSL AD certificate should now be imported into the UCS system using
the UMC module.

This is done by clicking on :guilabel:`Upload` in the sub menu *Active Directory
connection SSL configuration*. This opens a window in which a file can be
selected, which is being uploaded and integrated into the UCS AD Connector.

.. _ad-connector-restart:

Starting/Stopping the Active Directory Connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The connector can be started using *Start Active Directory connection service*
and stopped using *Stop Active Directory connection service*. Alternatively,
the starting/stopping can also be performed with the
:file:`/etc/init.d/univention-ad-connector` init-script.

.. _windows-functional-test-of-basic-settings:

Functional test of basic settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The correct basic configuration of the connector can be checked by searching in
Active Directory from the UCS system. Here one can search e.g. for the
administrator account in Active Directory with:

.. code-block:: console

   $ univention-adsearch cn=Administrator

As :command:`univention-adsearch` accesses the configuration saved in |UCSUCR|,
this allows you to check the reachability/configuration of the Active Directory
access.

.. _ad-connector-ad-password:

Changing the AD access password
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The access data required by the UCS AD Connector for Active Directory are
configured via the |UCSUCRV| :envvar:`connector/ad/ldap/binddn` and
:envvar:`connector/ad/ldap/bindpw`. If the password has changed or you wish to
use another user account, these variables must be adapted manually.

The |UCSUCRV| :envvar:`connector/ad/ldap/binddn` is used to configure the LDAP
DN of a privileged replication user. This must be a member of the ``Domain
Admins`` group in the AD. The corresponding password must be saved locally in a
file on the UCS system, the name of which must be entered in the |UCSUCRV|
:envvar:`connector/ad/ldap/bindpw`. The access rights for the file should be
restricted so that only the ``root`` owner has access. The following commands
show this as an example:

.. code-block:: console

   $ eval "$(ucr shell)"
   $ echo "Updating ${connector_ad_ldap_bindpw?}"
   $ echo "for AD sync user ${connector_ad_ldap_binddn?}"
   $ touch "${connector_ad_ldap_bindpw?}"
   $ chmod 600 "${connector_ad_ldap_bindpw?}"
   $ echo -n "Current AD Syncuser password" > "${connector_ad_ldap_bindpw?}"


.. _ad-connector-tools:

Additional tools / Debugging connector problems
-----------------------------------------------

The UCS AD Connector provides the following tools and log files for
diagnosis:

.. _ad-connector-univention-adsearch:

:command:`univention-adsearch`
   This tool facilitates a LDAP search in Active Directory. Objects
   deleted in AD are always shown (they are still kept in an LDAP subtree in
   AD). As the first parameter the script awaits an LDAP filter; the second
   parameter can be a list of LDAP attributes to be displayed.

   Example:

   .. code-block:: console

      $ univention-adsearch cn=administrator cn givenName

.. _ad-connector-univention-adconnector-list-rejected:

:command:`univention-adconnector-list-rejected`
   This tool lists the DNs of non-synchronized objects. In addition, in so far
   as temporarily stored, the corresponding DN in the respective other LDAP
   directory will be displayed. In conclusion ``lastUSN`` shows the ID of the
   last change synchronized by AD.

   This script may display an error message or an incomplete output if the AD
   connector is in operation.

.. _windows-logfiles:

Logfiles
   For troubleshooting when experiencing synchronization problems, corresponding
   messages can be found in the following files on the UCS system:


   * :file:`/var/log/univention/connector-ad.log`
   * :file:`/var/log/univention/connector-status.log`

.. _ad-connector-details-on-preconfigured-synchronization:

Details on preconfigured synchronization
----------------------------------------

All containers which are ignored due to corresponding filters are exempted from
synchronization as standard. This can be found in the
:file:`/etc/univention/connector/ad/mapping` configuration file under the
*global_ignore_subtree* setting. To except users from synchronization their user
name can be added to the |UCSUCRV|
:envvar:`connector/ad/mapping/user/ignorelist`. For more flexibility a filter
can be set in the |UCSUCRV| :envvar:`connector/ad/mapping/user/ignorefilter`.
However this filter does not support the full LDAP filter syntax. It is always
case sensitive and the placeholder ``*`` can only be used as a single value
without any other characters.

.. _ad-connector-containers-and-ous:

Containers and organizational units
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Containers and organizational units are synchronized together with their
description. In addition, the ``cn=mail`` and ``cn=kerberos`` containers are
ignored on both sides. Some particularities must be noted for containers on the
AD side. In the :guilabel:`User manager` Active Directory offers no possibility
to create containers, but displays them only in the advanced mode
(:menuselection:`View --> Advanced settings`).

Take the following particularities into account:

* Containers or organizational units deleted in AD are deleted recursively in
  UCS, which means that any non-synchronized subordinate objects, which are not
  visible in AD, are also deleted.

.. _ad-connector-groups:

Groups
~~~~~~

Groups are synchronized using the group name, whereby a user's primary group is
taken into account (which is only stored for the user in LDAP in AD).

Group members with no opposite in the other system, e.g., due to ignore filters,
are ignored (thus remain members of the group).

The description of the group is also synchronized.

.. rubric:: Particularities

Take the following particularities into account:

* The *pre Windows 2000 name* (LDAP attribute ``samAccountName``) is used in AD,
  which means that a group in Active Directory can appear under a different name
  from in UCS.

* The connector ignores groups, which have been configured as a *Well-Known
  Group* under :guilabel:`Samba group type` in |UCSUDM|. There is no
  synchronization of the SID or the RID.

* Groups which were configured as *Local Group* under :guilabel:`Samba group
  type` in |UCSUDM| are synchronized as a *global group* in the Active Directory
  by the connector.

* Newly created or moved groups are always saved in the same subcontainer on the
  opposite side. If several groups with the same name are present in different
  containers during initialization, the members are synchronized, but not the
  position in LDAP. If one of these groups is migrated on one side, the target
  container on the other side is identical, so that the DNs of the groups can no
  longer be differentiated from this point onward.

* Certain group names are converted using a mapping table so that, for example
  in a German language setup, the UCS group ``Domain Users`` is synchronized
  with the AD group *Domänen-Benutzer*. When used in anglophone AD domains, this
  mapping can result in *germanophone* groups' being created and should thus be
  deactivated in this case. This can be done using the |UCSUCRV|
  :envvar:`connector/ad/mapping/group/language`

  The complete table is:

  .. list-table::
     :header-rows: 1

     * - *UCS group*
       - *AD group*

     * - ``Domain Users``
       - ``Domänen-Benutzer``

     * - ``Domain Admins``
       - ``Domänen-Admins``

     * - ``Windows Hosts``
       - ``Domänencomputer``

* Nested groups are represented differently in AD and UCS. In UCS, if groups are
  members of groups, these objects can not always be synchronized on the AD side
  and appear in the list of rejected objects. Due to the existing limitations in
  Active Directory, nested groups should only be assigned there.

* If a global group :samp:`{A}` is accepted as a member of another global group
  :samp:`{B}` in |UCSUDM|, this membership does not appear in Active Directory
  because of the internal AD limitations in :program:`Windows 2000/2003`. If
  group :samp:`{A}`'s name is then changed, the group membership to group
  :samp:`{B}` will be lost. Since :program:`Windows 2008` this limitation no
  longer exists and thus global groups can also be nested in Active Directory.

.. _windows-groups-custommappings:

.. rubric:: Custom mappings

It is also possible to modify and append custom mappings. For that to work a
file has to be created named
:file:`/etc/univention/connector/ad/localmapping.py`. Within that file the
following function should be implemented:

.. code-block:: python

   def mapping_hook(ad_mapping):
       return ad_mapping

The contents of the :command:`ad_mapping` variable can be modified to influence
the mapping. The resulting mapping gets written to
:file:`/var/log/univention/connector-ad-mapping.log` when the |UCSADC| is
restarted.

.. _ad-connector-benutzer:

Users
~~~~~

Users are synchronized like groups using the username or using the AD pre
Windows 2000 name. The *First name*, *Last name*, *Primary group* (in so far as
present on the other side), *Organization*, *Description*, *Street*, *City*,
*Postal code*, *Windows home path*, *Windows login script*, *Disabled* and
*Account expiry date* attributes are transferred. Indirectly *Password*,
*Password expiry date* and *Change password on next login* are also
synchronized. *Primary email address* and *Telephone number* are prepared, but
commented out due to differing syntax in the mapping configuration.

The ``root`` and ``Administrator`` users are exempted.

.. _windows-user-particularities:

Take the following particularities into account:

* Users are also identified using the name, so that for users created before the
  first synchronization on both sides, the same process applies as for groups as
  regards the position in LDAP.

* In some cases, a user to be created under AD, for which the password has been
  rejected, is deleted from AD immediately after creation. The reasoning behind
  this is that AD created this user firstly and then deletes it immediately once
  the password is rejected. If these operations are transmitted to UCS, they are
  transmitted back to AD. If the user is re-entered on the AD side before the
  operation is transmitted back, it is deleted after the transmission. The
  occurrence of this process is dependent on the polling interval set for the
  connector.

* AD and UCS create new users in a specific primary group (usually ``Domain
  Users`` or ``Domänen-Benutzer``) depending on the presetting. During the
  first synchronization from UCS to AD the users are therefore always a member
  in this group.
