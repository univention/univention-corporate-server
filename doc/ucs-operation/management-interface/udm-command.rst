.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _management-interface-udm-command:

Command-line interface for domain management
============================================

.. highlight:: console

:program:`udm` is the command-line interface for domain management
in Univention Directory Manager (UDM).
Use it to automate administrative tasks in scripts
and to integrate domain management into other programs.
It's an alternative to the web-based *Management UI*
and its management modules.

Run the command as the ``root`` user on the :term:`Primary Directory Node`
with the :command:`univention-directory-manager` command,
or use the short form :command:`udm`.

UDM and the web interface use the same domain management modules.
As a result,
the command-line interface provides the same functions as the web interface.

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-management-reference`
      in :cite:t:`uv-nubus-manual`
      for the reference to the web-based management modules of UDM in the *Management UI*.

.. _management-interface-udm-command-parameters:

Parameters of the command-line interface
----------------------------------------

.. program:: udm

To list all available modules,
run the command shown in :numref:`udm-list-modules-listing`
with the ``modules`` parameter.

.. code-block::
   :caption: List available UDM modules
   :name: udm-list-modules-listing

   $ univention-directory-manager modules
   Available Modules are:
     computers/computer
     computers/domaincontroller_backup
     computers/domaincontroller_master
     computers/domaincontroller_slave
     [...]

Every module has the following operations:

.. option:: list, lookup

   Lists all existing objects of this type.

.. option:: create, new

   Creates a new object.

.. option:: modify, edit

   Modifies an existing object.

.. option:: remove, delete

   Deletes an object.

.. option:: move

   Moves an object to another position in the LDAP directory.

.. option:: restore

   Restores an object from the Recycle Bin.

To view the options and operations for a UDM module,
run the command shown in :numref:`udm-module-options-listing`
with the module name and the operation.

.. code-block::
   :caption: View options and operations for a UDM module
   :name: udm-module-options-listing

   $ univention-directory-manager users/user move
   [...]
   general options:
     --binddn                         bind DN
     --bindpwd                        bind password (deprecated, use --bindpwdfile instead)
     --bindpwdfile                    file containing bind password
   [...]
   create options:
     --position                       Set position in tree
     --set                            Set variable to value, e.g. foo=bar
   [...]
   modify options:
     --dn                             Edit object with DN
     --set                            Set variable to value, e.g. foo=bar
   [...]
   remove options:
     --dn                             Remove object with DN
     --superordinate                  Use superordinate module
   [...]
   list options:
     --filter                         Lookup filter
     --position                       Search underneath of position in tree
   [...]
   move options:
     --dn                             Move object with DN
     --position                       Move to position in tree
   [...]

To view all operations, options, and attributes for a module,
run the command shown in :numref:`udm-module-attributes-listing`.
Replace ``category/modulename`` with the module path,
for example, ``users/user``.

.. code-block::
   :caption: View all attributes for a UDM module
   :name: udm-module-attributes-listing

   $ univention-directory-manager [category/modulename]

When using the :option:`udm create` operation,
you must specify all attributes marked with ``*``.

Some attributes can have more than one value,
for example, email addresses for user objects.
The ``[]`` marker after an attribute name identifies a multi-value field.
Some attributes require specific options for the object.
To set an option for an individual attribute,
enter the option name,
as shown in :numref:`udm-module-variables-listing`.

.. code-block::
   :caption: View variables for a UDM module
   :name: udm-module-variables-listing

   users/user variables:
     General:
       username (*)                             Username
   [...]
     Contact:
       e-mail (person,[])                       E-Mail Address

Here, ``username (*)`` means that you must always set this attribute
when you create user objects.
When you enable the *person* option for the user account,
which is the default,
you can add one or more email addresses to the contact information.

The following common parameters are available,
depending on the operation:

.. option:: --binddn

   Use this parameter to specify the bind DN
   for the LDAP connection.

   .. important::

      You usually don't need ``--binddn``
      when you run :command:`udm` as ``root`` on a Nubus for UCS system.
      In that case,
      UDM tries to use local system credentials automatically.

      Provide ``--binddn``
      when you want to authenticate as a different LDAP account
      or when the default local credentials aren't available
      or don't have the required permissions.

.. option:: --bindpwd

   Use this parameter to specify the bind password
   for the LDAP connection.

   .. deprecated:: 5.2-4
      ``--bindpwd`` is deprecated.
      Use :option:`--bindpwdfile` instead.

.. option:: --bindpwdfile

   Use this parameter to specify a file
   that contains the bind password for :option:`--binddn`.

   .. important::

      You usually don't need ``--bindpwdfile``
      when you run :command:`udm` as ``root`` on a UCS system.
      If you don't enter bind credentials,
      UDM tries to use local system credentials,
      such as the administrator account
      or the machine account.

      Provide :option:`--bindpwdfile`
      together with :option:`--binddn`
      when you want to authenticate explicitly
      or when automatic local authentication isn't available.

.. option:: --logfile

   Use this parameter to specify the path of the log file
   for the command.
   If you don't enter ``--logfile``,
   UDM writes to
   :file:`/var/log/univention/directory-manager-cmd.log`.

.. option:: --tls

   Use this parameter to control StartTLS for the LDAP connection.

   ``0``
      Don't use StartTLS.

   ``1``
      Try StartTLS.

   ``2``
      Require StartTLS.
      This is default behavior, if you don't provide :option:`--tls`.

.. option:: --dn

   Use this parameter to specify the distinguished name (DN) of the object
   when you modify, delete, move, or restore it.
   Enter the complete DN,
   as shown in :numref:`udm-remove-object-by-dn-listing`.

   .. code-block::
      :caption: Remove an object by DN
      :name: udm-remove-object-by-dn-listing

      $ univention-directory-manager users/user remove \
        --dn "uid=ldapadmin,cn=users,dc=company,dc=example"

.. option:: --position

   Use this parameter to specify an LDAP position.

   In the :option:`udm create` operation,
   this parameter specifies where UDM creates the object.
   If you don't enter ``--position``,
   UDM creates the object under the module's default LDAP base.
   If you use :option:`--superordinate` without ``--position``,
   UDM uses the superordinate DN as the position.

   In the :option:`udm list` operation,
   this parameter limits the search to objects below the specified LDAP position.

   In the :option:`udm move` operation,
   this parameter specifies the target position,
   as shown in :numref:`udm-move-object-by-position-listing`.

   .. code-block::
      :caption: Move an object to another LDAP position
      :name: udm-move-object-by-position-listing

      $ univention-directory-manager computers/ipmanagedclient move \
        --dn "cn=desk01,cn=management,cn=computers,dc=company,dc=com" \
        --position "cn=finance,cn=computers,dc=company,dc=example"

.. option:: --set

   Use this parameter to assign the given value to the following attribute.
   Use one ``--set`` parameter for each attribute-value pair,
   as shown in :numref:`udm-set-attribute-values-listing`.

   .. code-block::
      :caption: Create a user with attribute values
      :name: udm-set-attribute-values-listing

      $ univention-directory-manager users/user create \
        --position "cn=users,dc=company,dc=example" \
        --set username="jsmith" \
        --set firstname="John" \
        --set lastname="Smith" \
        --set password="12345678"

.. option:: --append, --remove

   Use ``--append`` or ``--remove`` to add or remove a value from a
   multi-value field,
   as shown in :numref:`udm-append-remove-values-listing`.

   .. code-block::
      :caption: Add and remove values in a multi-value field
      :name: udm-append-remove-values-listing

      $ univention-directory-manager groups/group modify \
        --dn "cn=staff,cn=groups,dc=company,dc=example" \
        --append users="uid=smith,cn=users,dc=company,dc=example" \
        --remove users="uid=miller,cn=users,dc=company,dc=example"

.. option:: --option

   Use this parameter to define the LDAP object classes for an object.
   For example,
   if you provide only the ``pki`` option for a user object,
   you can't specify ``mailPrimaryAddress``
   because this attribute belongs to the ``mail`` option.

.. option:: --append-option, --remove-option

   Use ``--append-option`` to add a module option
   to the current option set.

   Use ``--remove-option`` to remove a module option
   from the current option set.

   These parameters are useful when a module provides default options,
   and you want to adjust them for one command.

.. option:: --superordinate

   Use ``--superordinate`` when an object requires the DN of a parent object.
   For example,
   a DHCP object requires a DHCP service object.
   Pass the DN of that object with the ``--superordinate`` option.

   For list operations,
   you can also use ``--superordinate`` to limit the lookup context
   for dependent objects.

.. option:: --policy-reference

   Use the ``--policy-reference`` parameter to assign a policy to an object.
   If you link a policy to an object,
   the object uses the policy settings,
   as shown in :numref:`udm-policy-reference-listing`.
   Replace ``category/modulename`` with the module path,
   and replace ``Operation`` with the operation that you want to run.

   Repeat the parameter to assign more than one policy.

   .. code-block::
      :caption: Assign a policy to an object
      :name: udm-policy-reference-listing

      $ univention-directory-manager [category/modulename] [Operation] \
        --policy-reference "cn=sales,cn=pwhistory,cn=users,cn=policies,dc=company,dc=example"

.. option:: --policy-dereference

   Use the ``--policy-dereference`` parameter to remove a policy from an object.

   Repeat the parameter to remove more than one policy reference.

.. option:: --ignore_exists

   The ``--ignore_exists`` parameter skips existing objects.
   If the object already exists,
   UDM still returns the error code ``0`` for no error.

.. option:: --ignore_not_exists

   Use this parameter with the :option:`udm modify` or :option:`udm remove` operation
   to ignore missing objects.
   If the object doesn't exist,
   UDM doesn't report an error.

.. option:: --remove_referring

   Use this parameter with the :option:`udm remove` operation
   to remove referring objects during cleanup,
   if the module supports that cleanup.

.. option:: --filter

   Use this parameter to select objects with an LDAP filter.

   With the :option:`udm list` operation,
   UDM lists matching objects.

   With the :option:`udm remove` operation,
   UDM removes the matching object in the selected context.
   You can combine ``--filter`` with :option:`--dn`
   or :option:`--position`.

.. option:: --policies

   Use this parameter with the :option:`udm list` operation
   to show policy-based settings.

   If you don't enter ``--policies``,
   UDM doesn't show policy-based settings.

   ``0``
      Show a short form.

   ``1``
      Show a long form that includes the policy DN.

.. option:: --properties

   Use this parameter with the :option:`udm list` operation
   to limit the output to specific properties.

   Repeat the parameter for each property that you want to show.
   If you don't enter ``--properties``,
   UDM shows all properties that are configured for list output.

.. _management-interface-udm-command-examples:

Command-line interface examples
-------------------------------

Use these examples as templates for your own scripts.

.. _management-interface-udm-command-examples-users:

Users
~~~~~

This section lists examples of the :command:`udm` working
with the :external+uv-nubus-manual:ref:`nubus-user-management-users`.

* To create a user in the standard user container,
  run the :option:`udm create` command shown in :numref:`udm-create-user-listing`.

  .. code-block::
     :caption: Create a user in the standard user container
     :name: udm-create-user-listing

     $ univention-directory-manager users/user create \
       --position "cn=users,dc=example,dc=com" \
       --set username="user01" \
       --set firstname="Random" \
       --set lastname="User" \
       --set organisation="Example company LLC" \
       --set mailPrimaryAddress="mail@example.com" \
       --set password="secretpassword"

* To add a postal address for an existing user,
  run the :option:`udm modify` command shown in :numref:`udm-add-user-postal-address-listing`.

  .. code-block::
     :caption: Add a postal address to an existing user
     :name: udm-add-user-postal-address-listing

     $ univention-directory-manager users/user modify \
       --dn "uid=user01,cn=users,dc=example,dc=com" \
       --set street="Exemplary Road 42" \
       --set postcode="28239" \
       --set city="Bremen"

* To list all users whose username begins with ``user``,
  run the :option:`udm list` command shown in :numref:`udm-list-users-by-prefix-listing`.

  .. code-block::
     :caption: List users by username prefix
     :name: udm-list-users-by-prefix-listing

     $ univention-directory-manager users/user list \
       --filter uid='user*'

* To limit the search to a specific LDAP position,
  run the :option:`udm list` command shown in :numref:`udm-list-users-by-prefix-position-listing`.
  This example lists all users in the ``cn=bremen,cn=users,dc=example,dc=com`` container.

  .. code-block::
     :caption: List users by username prefix in a specific container
     :name: udm-list-users-by-prefix-position-listing

     $ univention-directory-manager users/user list \
       --filter uid="user*" \
       --position "cn=bremen,cn=users,dc=example,dc=com"

* To remove the user ``user04``,
  run the :option:`udm remove` command shown in :numref:`udm-remove-user-listing`.

  .. code-block::
     :caption: Remove a user
     :name: udm-remove-user-listing

     $ univention-directory-manager users/user remove \
       --dn "uid=user04,cn=users,dc=example,dc=com"

* If your organization has two sites with separate containers,
  you can move a user from the ``Hamburg`` container
  to the ``Bremen`` container.
  Run the :option:`udm move` command shown in :numref:`udm-move-user-between-containers-listing`.

  .. code-block::
     :caption: Move a user between site containers
     :name: udm-move-user-between-containers-listing

     $ univention-directory-manager users/user move \
       --dn "uid=user03,cn=hamburg,cn=users,dc=example,dc=com" \
       --position "cn=bremen,cn=users,dc=example,dc=com"

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-user-management-users`
      in :cite:t:`uv-nubus-manual`
      for information about the *Users* management module.

.. _management-interface-udm-command-examples-groups:

Groups
~~~~~~

This section lists examples of the :command:`udm` working
with the :external+uv-nubus-manual:ref:`nubus-groups-management`.

* To create the group ``Example Users`` and add the user ``user01``,
  run the :option:`udm create` command shown in :numref:`udm-create-group-with-user-listing`.

  .. code-block::
     :caption: Create a group and add a user
     :name: udm-create-group-with-user-listing

     $ univention-directory-manager groups/group create \
       --position "cn=groups,dc=example,dc=com" \
       --set name="Example Users" \
       --set users="uid=user01,cn=users,dc=example,dc=com"

* To add the user ``user02`` to the existing group,
  run the :option:`udm modify` command shown in :numref:`udm-add-user-to-group-listing`.

  .. code-block::
     :caption: Add a user to an existing group
     :name: udm-add-user-to-group-listing

     $ univention-directory-manager groups/group modify \
       --dn "cn=Example Users,cn=groups,dc=example,dc=com" \
       --append users="uid=user02,cn=users,dc=example,dc=com"

  .. caution::

     A ``--set`` on the attribute ``users`` overwrites the list of group members
     in contrast to ``--append``.

* To remove the user ``user01`` from the group,
  run the :option:`udm modify` command shown in :numref:`udm-remove-user-from-group-listing`.

  .. code-block::
     :caption: Remove a user from a group
     :name: udm-remove-user-from-group-listing

     $ univention-directory-manager groups/group modify \
       --dn "cn=Example Users,cn=groups,dc=example,dc=com" \
       --remove users="uid=user01,cn=users,dc=example,dc=com"

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-groups-management`
      in :cite:t:`uv-nubus-manual`
      for information about the *Groups* management module.

.. _management-interface-udm-command-examples-containers:

Containers
~~~~~~~~~~

To create the ``cn=Bremen`` container under ``cn=computers``
for computers at the ``Bremen`` site,
run the :option:`udm create` command shown in :numref:`udm-create-container-listing`.
The ``computerPath`` option also registers this container
as the standard container for computer objects.
For more information, see :external+uv-nubus-manual:ref:`nubus-domain-ldap-user-defined-structure`
in :cite:t:`uv-nubus-manual`.

.. code-block::
   :caption: Create a container for a site
   :name: udm-create-container-listing

   $ univention-directory-manager container/cn create \
     --position "cn=computers,dc=example,dc=com" \
     --set name="bremen" \
     --set computerPath=1

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-domain-ldap`
      in :cite:t:`uv-nubus-manual`
      for information about the *LDAP directory* management module.

.. _management-interface-udm-command-examples-policies:

Policies
~~~~~~~~

This section lists examples of the :command:`udm` working
with the :external+uv-nubus-manual:ref:`nubus-domain-policies`.

* To create a user quota policy,
  run the :option:`udm create` command shown in :numref:`udm-create-user-quota-policy-listing`.

  .. code-block::
     :caption: Create a user quota policy
     :name: udm-create-user-quota-policy-listing

     $ univention-directory-manager policies/share_userquota create \
       --position "cn=policies,dc=example,dc=com" \
       --set name="Default quota" \
       --set softLimitSpace=5GB \
       --set hardLimitSpace=10GB

* To link this policy to the user container ``cn=users``,
  run the :option:`udm modify` command shown in :numref:`udm-link-policy-to-user-container-listing`.

  .. code-block::
     :caption: Link a policy to the user container
     :name: udm-link-policy-to-user-container-listing

     $ univention-directory-manager container/cn modify \
       --dn "cn=users,dc=example,dc=com" \
       --policy-reference "cn=Default quota,cn=policies,dc=example,dc=com"

* To create a *Univention Configuration Registry* policy
  that sets the storage time for log files to one year,
  run the :option:`udm create` command shown in :numref:`udm-create-ucr-policy-listing`.
  Use one space to separate the variable name from its value.

  .. code-block::
     :caption: Create a UCR policy
     :name: udm-create-ucr-policy-listing

     $ univention-directory-manager policies/registry create \
       --position "cn=config-registry,cn=policies,dc=example,dc=com" \
       --set name="default UCR settings" \
       --set registry="logrotate/rotate/count 52"

* To add another value to the UCR policy,
  run the :option:`udm modify` command shown in :numref:`udm-append-ucr-policy-value-listing`.

  .. code-block::
     :caption: Add a value to a UCR policy
     :name: udm-append-ucr-policy-value-listing

     $ univention-directory-manager policies/registry modify \
       --dn "cn=default UCR settings,cn=config-registry,cn=policies,dc=example,dc=com" \
       --append registry='"logrotate/compress" "no"'

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-domain-policies`
      in :cite:t:`uv-nubus-manual`
      for information about the *Policies* management module.

.. _management-interface-udm-command-examples-computers:

Computers
~~~~~~~~~

To create a Windows client account,
run the :option:`udm create` command shown in :numref:`udm-create-windows-client-listing`.
If the client joins the Samba domain later,
as described in :ref:`domain-infrastructure-join-windows`,
the domain join uses this computer account automatically:

.. code-block::
   :caption: Create a Windows client account
   :name: udm-create-windows-client-listing

   $ univention-directory-manager computers/windows create \
     --position "cn=computers,dc=example,dc=com" \
     --set name=WinClient01 \
     --set mac=aa:bb:cc:aa:bb:cc \
     --set ip=192.0.2.10

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-computer-management`
      in :cite:t:`uv-nubus-manual`
      for information about the *Computers* management module.

.. _management-interface-udm-command-examples-shares:

Shares
~~~~~~

To create the *Documentation* share on *fileserver.example.com*,
run the :option:`udm create` command shown in :numref:`udm-create-share-listing`.
If the :file:`/var/shares/documentation/` directory doesn't exist on the server,
UDM creates it automatically.

.. code-block::
   :caption: Create a share
   :name: udm-create-share-listing

   $ univention-directory-manager shares/share create \
     --position "cn=shares,dc=example,dc=com" \
     --set name="Documentation" \
     --set host="fileserver.example.com" \
     --set path="/var/shares/documentation"

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-domain-shares`
      in :cite:t:`uv-nubus-manual`
      for information about the *Shares* management module.

.. _management-interface-udm-command-examples-printers:

Printers
~~~~~~~~

To create the printer share *LaserPrinter01* on the print server
*printserver.example.com*,
run the :option:`udm create` command shown in :numref:`udm-create-printer-share-listing`.
The PPD file defines the printer properties.
Specify the PPD filename relative to :file:`/usr/share/ppd/`.
Ensure the printer is reachable over the network and supports the IPP protocol.

.. code-block::
   :caption: Create a printer share
   :name: udm-create-printer-share-listing

   $ univention-directory-manager shares/printer create \
     --position "cn=printers,dc=example,dc=com" \
     --set name="LaserPrinter01" \
     --set spoolHost="printserver.example.com" \
     --set uri="ipp:// 192.0.2.100" \
     --set model="foomatic-rip/HP-Color_LaserJet_9500-Postscript.ppd" \
     --set location="Head office" \
     --set producer="producer: cn=HP,cn=cups,cn=univention,dc=example,dc=com"

.. note::

   Include a blank space between the print protocol
   and the target path in the ``uri`` parameter.
   For a list of print protocols,
   see :external+uv-nubus-manual:ref:`nubus-devices-printers-tab-general-field-protocol`
   in :cite:t:`uv-nubus-manual`.

You can group printers in a printer group to streamline administration.
For more information about printer groups,
see :external+uv-nubus-manual:ref:`nubus-devices-printers-groups`.
Before creating a printer group,
ensure the printer shares you want to add already exist.
To create a printer group,
run the :option:`udm create` command shown in :numref:`udm-create-printer-group-listing`.

.. code-block::
   :caption: Create a printer group
   :name: udm-create-printer-group-listing

   $ univention-directory-manager shares/printergroup create \
     --position "cn=printers,dc=example,dc=com" \
     --set name=LaserPrinters \
     --set spoolHost="printserver.example.com" \
     --append groupMember=LaserPrinter01 \
     --append groupMember=LaserPrinter02

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-devices-printers`
      in :cite:t:`uv-nubus-manual`
      for information about the *Printers* management module.

.. _management-interface-udm-command-examples-dns-dhcp:

DNS and DHCP
~~~~~~~~~~~~

To configure an IP assignment through DHCP,
register a DHCP computer entry for the MAC address,
as shown in :numref:`udm-create-dhcp-host-listing`.
For more information about DHCP,
see :external+uv-ucs-manual:ref:`module-dhcp-dhcp`.

.. TODO: Update link to UCS Manual after referenced section is migrated.

.. code-block::
   :caption: Create a DHCP host entry
   :name: udm-create-dhcp-host-listing

   $ univention-directory-manager dhcp/host create \
     --superordinate "cn=example.com,cn=dhcp,dc=example,dc=com" \
     --set host="Client222" \
     --set fixedaddress="192.0.2.110" \
     --set hwaddress="ethernet 00:11:22:33:44:55"

To resolve a computer name through DNS,
use the commands shown in :numref:`udm-create-dns-host-record-listing`
and :numref:`udm-create-dns-ptr-record-listing`
to configure forward resolution with a host record
and reverse resolution with a PTR record.
For more information about DNS,
see :external+uv-ucs-manual:ref:`networks-dns`.

.. TODO: Update link to UCS Manual after referenced section is migrated.

.. code-block::
   :caption: Create a DNS host record
   :name: udm-create-dns-host-record-listing

   $ univention-directory-manager dns/host_record create \
     --superordinate "zoneName=example.com,cn=dns,dc=example,dc=com" \
     --set name="Client222" \
     --set a="192.0.2.110"

.. code-block::
   :caption: Create a DNS PTR record
   :name: udm-create-dns-ptr-record-listing

   $ univention-directory-manager dns/ptr_record create \
     --superordinate "zoneName=0.168.192.in-addr.arpa,cn=dns,dc=example,dc=com" \
     --set address="110" \
     --set ptr_record="Client222.example.com."

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-domain-dhcp`
      in :cite:t:`uv-nubus-manual`
      for information about the *DHCP* management module.

   :external+uv-nubus-manual:ref:`nubus-domain-dns`
      in :cite:t:`uv-nubus-manual`
      for information about the *DNS* management module.

.. _management-interface-udm-command-examples-extended-attributes:

Extended attributes
~~~~~~~~~~~~~~~~~~~

Use extended attributes to add fields to management modules in the *Management UI*.
For more information, see :external+uv-nubus-manual:ref:`nubus-domain-extended-attributes`.
To add a new attribute that stores the license plate number of a company car for each user,
run the :option:`udm create` command shown in :numref:`udm-create-extended-attribute-listing`.
The object class ``univentionFreeAttributes`` stores these values.

.. code-block::
   :caption: Create an extended attribute
   :name: udm-create-extended-attribute-listing

   $ univention-directory-manager settings/extended_attribute create \
     --position "cn=custom attributes,cn=univention,dc=example,dc=com" \
     --set name="CarLicense" \
     --set module="users/user" \
     --set ldapMapping="univentionFreeAttribute1" \
     --set objectClass="univentionFreeAttributes" \
     --set longDescription="License plate number of the company car" \
     --set tabName="Company car" \
     --set multivalue=0 \
     --set syntax="string" \
     --set shortDescription="Car license"

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-domain-extended-attributes`
      in :cite:t:`uv-nubus-manual`
      for information about how to expand management modules.

