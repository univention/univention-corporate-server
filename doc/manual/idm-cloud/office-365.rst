.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _idmcloud-o365:

Microsoft 365 Connector
=======================

The synchronization of users and groups and teams to an Azure Directory Domain,
which will then be used by Microsoft 365, is made possible by the
:program:`Microsoft Office Connector`. The connector makes it possible to
control which of the users created in UCS can use Microsoft 365. The selected
users will be provisioned accordingly into the Azure Active Directory domain. It
is configurable which user attributes are synchronized and which are anonymized
during synchronization.

The single sign-on login to Microsoft 365 is done via the UCS integrated SAML
implementation. Authentication takes place against the UCS server, and no
password hashes are transmitted to Microsoft Azure Cloud. The user's
authentication is done exclusively via the client's web browser. The web browser
should however be able to resolve the DNS records of the UCS domain, this is a
particularly important point to note for mobile devices.

.. _idmcloud-o365-setup:

Setup
-----

To setup the Microsoft 365 Connector a Microsoft 365 Administrator account, a
corresponding Account in the Azure Active Directory, as well as a `Domain
verified by Microsoft <microsoft-domain-verify_>`_ are required. The first two
are provided for test purposes by Microsoft for free. However to configure the
SSO, a separate internet domain where TXT records can be created is required.

In case there is no Microsoft 365 subscription available, one can be configured
it via https://www.office.com/ in the *trial for business* section. A connection
is not possible with a private Microsoft account.

You should then sign in with a *Microsoft 365 Administrator Account* into the
:guilabel:`Microsoft 365 Admin Center`. At the bottom left of the navigation bar
select :guilabel:`Azure AD` to open the *Azure Management Portal* in a new
window.

In the *Azure Active Directory* section the menu item :guilabel:`Custom domain
names` can be used to add and verify your own domain. For this it is necessary
to create a TXT record in the DNS of your own domain. This process can take up
to several minutes. Afterwards the *status* of the configured domain will be
displayed as **Verified**.

Now the :program:`Microsoft 365 Connector` App can be installed from the App
Center on the UCS system. The installation takes a few minutes. There is a setup
wizard available for the initial configuration. After completing the wizard the
connector is ready for use.

.. _idmcloud-o365-wizard:

.. figure:: /images/office_wizard1.*
   :alt: Microsoft 365 Setup assistant

   Microsoft 365 Setup assistant

.. _idmcloud-o365-config:

Configuration
-------------

After the end of the installation through the setup wizard, users can be enabled
to use Microsoft 365. This configuration can be done through the user module on
each user object on the *Microsoft 365* tab. Usage and allocation of licenses
are acknowledged in the *Microsoft 365 Admin Center*.

.. _idmcloud-o365-users:

Users
~~~~~

If a change is made to the user, the changes are likewise replicated to the
Azure Active Directory domain. There is no synchronization from the Azure Active
Directory to the UCS system. This means changes made in Azure Active Directory
or Office Portal may be overridden by changes to the same attributes in UCS.

Due to Azure Active Directory security policies, users or groups in the Azure AD
can't be deleted during synchronization. They are merely disabled and renamed.
The licenses are revoked in the Azure Active Directory so that they become
available to other users. Users and groups whose names start with
``ZZZ_deleted`` can be deleted in *Microsoft 365 Admin Center*.

It is necessary to configure a country for the user in Microsoft 365. The
connector uses the specification of the country from the contact data of the
user. If not set, it uses the setting of the server. With the help of |UCSUCRV|
:envvar:`office365/attributes/usageLocation` a 2-character abbreviation, e.g.
``US``, can be set as the default.

Through |UCSUCRV| :envvar:`office365/attributes/sync`, the LDAP attributes (e.g.
first name, last name, etc.) of a user's account which will to be synchronized
are configured. The form is a comma-separated list of LDAP attributes. Thus
adaptation to personal needs is possible.

With the |UCSUCRV| :envvar:`office365/attributes/anonymize`, a comma-separated
list of LDAP attributes can be configured that are created in the Azure Active
Directory but filled with random values. The |UCSUCRVs|
:envvar:`office365/attributes/static/.*` allows the filling of attributes on the
Microsoft side with a predefined value.

The |UCSUCRV| :envvar:`office365/attributes/never` can be used to specify a
comma separated list of LDAP attributes that should not be synchronized even
when they appear in :envvar:`office365/attributes/sync` or
:envvar:`office365/attributes/anonymize`.

The |UCSUCRVs| :envvar:`office365/attributes/mapping/.*` define a mapping of
UCS LDAP attributes to Azure Attributes. Usually these variables don't need to
be changed. The synchronization of the groups of Microsoft 365 user can be
enabled with the |UCSUCRV| :envvar:`office365/groups/sync`.

Changes to |UCSUCRVs| are implemented only after restarting the |UCSUDL|.

.. _idmcloud-o365-groups:

Groups
~~~~~~

The :program:`Microsoft 365 Connector` can synchronize groups to Microsoft Azure Active Directory.
The connector synchronizes a group,
if it contains at least one user that's enabled for *Microsoft 365*.
By default, the connector creates the group as a ``Security Group`` in *Microsoft 365*.

You can enable the synchronization by setting
the |UCSUCRV| :envvar:`office365/groups/sync` to ``yes``.

.. versionadded:: 5.0-7-erratum-1060

   With :uv:erratum:`5.0x1060`, you can change the group type to ``Microsoft 365 Group``
   in the UMC on the *Microsoft 365* tab.

   If the UCS system with the connector installed doesn't have at least this version level,
   you can't change the group type.

When you change the group type,
the connector deletes the existing group in *Microsoft 365*,
and it creates a group with the group type you defined.
*Microsoft 365* doesn't allow to change the group type property of an existing group.
The connector adds the group members to the group,
and if the group is a *Microsoft 365 Team*,
the connector also creates the team.

.. caution::

   Changing the group type can effect the group's permissions and settings in *Microsoft 365*.
   Change group types with caution.

You can change the default group type of a Microsoft 365 group.
The following group types are available:

* ``Security``
* ``Microsoft 365 Group``

To change the group type,
you need to modify the default value
of the extended attribute ``UniventionMicrosoft365GroupType`` to one of the available group types:

.. code-block:: console

    $ udm settings/extended_attribute modify \
         --dn "cn=UniventionMicrosoft365GroupType,cn=custom attributes,cn=univention,$(ucr get ldap/base)" \
         --set default="Microsoft 365 Group"

.. _idmcloud-o365-teams:

Teams
~~~~~

To use Teams, synchronization of groups must be enabled in the |UCSUCRV|
:envvar:`office365/groups/sync` with the value ``yes``, and then the |UCSUDL|
service must be restarted. If UCS groups are to be created as teams in Microsoft
365, the groups must be configured as teams on the *Microsoft 365* tab via the
:guilabel:`Microsoft 365 Team` checkbox. Furthermore, it is necessary to define
an owner of the team on the same tab. Further settings on the team can be made
by the team owners directly in the Teams interface. After activating a group as
a team, the group members are added to the new team. Provisioning a new team in
Microsoft 365 can take a few minutes.

Ensure that users of a team in Azure are provided with a license that includes
the use of Teams.

.. _idmcloud-o365-multipleconnections:

Synchronization of Users in multiple Azure Active Directories
-------------------------------------------------------------

The Microsoft 365 Connector is able to synchronize users to multiple Azure
Active Directories. For each user account, multiple Azure AD instances can be
assigned, where an account should be created. A user gets a distinct username
(*Userprincipalname* or *UPN*) for every assigned Azure AD.

An alias is assigned to each additional Azure AD connection by the
administrator. To manage these aliases the program
:command:`/usr/share/univention-office365/scripts/manage_adconnections` can be
used. A new alias is created by calling
:samp:`/usr/share/univention-office365/scripts/manage_adconnections create
{<Aliasname>}`. This will set the |UCSUCRV|
:envvar:`office365/adconnection/wizard` to the newly created alias. The value of
this |UCSUCRV| defines which connection is configured by the next run of the
Microsoft 365 Configuration Wizard.

After creating the alias, the new connection must be configured through
the Microsoft 365 Configuration Wizard, as well.

To use single sign-on with multiple Azure AD connections, a new logical
SAML Identity Provider is needed for each connection. This is described
in :ref:`domain-saml-extended-configuration`.

The Identity Provider should get the same name as the alias. If another name was
chosen, the PowerShell script to configure single sign-on needs to be adjusted
manually. For example the |UCSUCRV|
:samp:`saml/idp/entityID/supplement/{Aliasname}=true` needs to be set on all
domain controllers responsible for single sign-on.

A UCS user can only use one Microsoft 365 account in one browser session
at a time. To change the connection, a logout from Microsoft 365 is
necessary.

A default alias for Microsoft 365 enabled users and groups can be set in the
|UCSUCRV| :envvar:`office365/defaultalias`. To synchronize them into a different
Azure Active Directory the connection alias must be selected explicitly at the
user or group object.

.. _idmcloud-o365-debug:

Troubleshooting/Debugging
-------------------------

Messages during the setup are logged in
:file:`/var/log/univention/management-console-module-office365.log`.

In case of synchronization problems, the log file of the |UCSUDL| should
be examined: :file:`/var/log/univention/listener.log`.

Some actions of the Connector use long-running Azure Cloud operations,
especially when using Teams. These operations are logged in the log file
:file:`/var/log/univention/listener_modules/ms-office-async.log`
The |UCSUCRV| :envvar:`office365/debug/werror` activates
additional debug output.
