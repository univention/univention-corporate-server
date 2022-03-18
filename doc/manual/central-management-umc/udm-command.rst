.. _central-udm:

Command line interface of domain management (|UCSUDM|)
======================================================

The |UCSUDM| is the command line interface alternative to the web-based
interface of the domain management UMC modules. It functions as a powerful tool
for the automation of administrative procedures in scripts and for the
integration in other programs.

|UCSUDM| can be started with the :command:`univention-directory-manager` command
(short form :command:`udm`) as the ``root`` user on the |UCSPRIMARYDN|.

UMC modules and |UCSUDM| use the same domain management modules, i.e., all
functions of the web interface are also available in the command line interface.

.. _central-udm-parms:

Parameters of the command line interface
----------------------------------------

.. program:: udm

A complete list of available modules is displayed if the :command:`udm`` is run
with the ``modules`` parameter:

.. code-block:: console

   $ univention-directory-manager modules
   Available Modules are:
     computers/computer
     computers/domaincontroller_backup
     computers/domaincontroller_master
     computers/domaincontroller_slave
     [...]

There are up to five operations for every module:

list
   lists all existing objects of this type.

create
   creates a new object.

modify
   or the *editing* of existing objects.

remove
   deletes an object.

move
   is used to move an object to another position in the LDAP directory.

The possible options of a UDM module and the operations which can be used on it
can be output by specifying the operation name, e.g.,

.. code-block:: console

   $ univention-directory-manager users/user move
   [...]
   general options:
     --binddn                         bind DN
     --bindpwd                        bind password
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


The following command outputs further information, the operations and the
options for every module. This also displays all attributes of the module:

.. code-block::

   univention-directory-manager [category/modulename]


With the ``create`` operation, the attributes marked with ``*`` must be
specified when creating a new object.

Some attributes can be assigned more than one value (e.g., mail addresses to
user objects). These multi-value fields are marked with ``[]`` behind the
attribute name. Some attributes can only be set if certain options are set for
the object. This is performed for the individual attributes by entering the
option name:

.. code-block::

   users/user variables:
     General:
       username (*)                             Username
   [...]
     Contact:
       e-mail (person,[])                       E-Mail Address


Here, ``username (*)`` signifies that this attribute must always be set when
creating user objects. If the *person* option is set for the user account (this
is the standard case), one or more e-mail addresses can be added to the contact
information.

A range of standard parameters are defined for every module:

.. highlight:: console

.. option:: --dn

   The parameter is used to specify the LDAP
   position of the object during modifications or deletion. The complete
   DN must be entered, e.g.,

   .. code-block::

      $ univention-directory-manager users/user remove \
      > --dn "uid=ldapadmin,cn=users,dc=company,dc=example"

.. option:: --position

   The parameter is used to specify at which LDAP position an object should be
   created. If no ``--position`` is entered, the object is created below the
   LDAP base! In the ``move`` operation, this parameter specifies to which
   position an object should be moved, e.g:

   .. code-block::

      $ univention-directory-manager computers/ipmanagedclient move \
      > --dn "cn=desk01,cn=management,cn=computers,dc=company,dc=com" \
      > --position "cn=finance,cn=computers,dc=company,dc=example"

.. option:: --set

   The parameter specifies that the given value should be assigned to the
   following attribute. The parameter must be used per attribute value pair,
   e.g:

   .. code-block::

      $ univention-directory-manager users/user create \
      > --position "cn=users,dc=compaby,dc=example" \
      > --set username="jsmith" \
      > --set firstname="John" \
      > --set lastname="Smith" \
      > --set password="12345678"

.. option:: --option

   The parameter defines the LDAP object classes of an object. If, for example,
   only ``pki`` is provided as options for a user object, it is not possible to
   specify a ``mailPrimaryAddress`` for this user as this attribute is part of
   the ``mail`` option:

.. option:: --superordinate

   ``--superordinate`` is used to specify dependent, superordinate modules. A
   DHCP object, for example, requires a DHCP service object under which it can
   be stored. This is transferred with the ``--superordinate`` option.

.. option:: --policy-reference

   The ``--policy-reference`` parameter allows the assignment of policies to
   objects (and similarly their deletion with ``--policy-dereference``). If a
   policy is linked to an object, the settings from the policy are used for the
   object, e.g.:

   .. code-block:: console

      $ univention-directory-manager [category | modulename] [Operation] \
      > --policy-reference "cn=sales,cn=pwhistory," \
      > "cn=users,cn=policies,dc=company,dc=example"

.. option:: --ignore-exists

   The ``--ignore_exists`` parameters skips existing objects. If it is not
   possible to create an object, as it already exists, the error code ``0`` (no
   error) is still returned.

.. option:: --append

   ``--append`` and ``--remove`` are used to add/remove a value from a
   multi-value field, e.g.:

   .. code-block:: console

      $ univention-directory-manager groups/group modify \
      > --dn "cn=staff,cn=groups,dc=company,dc=example" \
      > --append users="uid=smith,cn=users,dc=company,dc=example" \
      > --remove users="uid=miller,cn=users,dc=company,dc=example"

.. option:: --remove

   See :option:`--append`.


.. _central-udm-example:

Example invocations of the command line interface
-------------------------------------------------

The following examples for the command line front end of |UCSUDM| can be used as
templates for your own scripts.

.. _central-udm-example-users:

Users
~~~~~

Creating a user in the standard user container:

.. code-block::

   $ univention-directory-manager users/user create \
   > --position "cn=users,dc=example,dc=com" \
   > --set username="user01" \
   > --set firstname="Random" \
   > --set lastname="User" \
   > --set organisation="Example company LLC" \
   > --set mailPrimaryAddress="mail@example.com" \
   > --set password="secretpassword"

Subsequent addition of the postal address for an existing user:

.. code-block::

   $ univention-directory-manager users/user modify \
   > --dn "uid=user01,cn=users,dc=example,dc=com" \
   > --set street="Exemplary Road 42" \
   > --set postcode="28239" \
   > --set city="Bremen"

This command can be used to display all the users whose user name begins with
*user*:

.. code-block::

   $ univention-directory-manager users/user list \
   > --filter uid=user*

Searching for objects with the ``--filter`` can also be limited to a position in
the LDAP directory; in this case, to all users in the container
``cn=bremen,cn=users,dc=example,dc=com``:

.. code-block::

   $ univention-directory-manager users/user list \
   > --filter uid="user*" \
   > --position "cn=bremen,cn=users,dc=example,dc=com"

This call removes the user ``user04``:

.. code-block::

   $ univention-directory-manager users/user remove \
   > --dn "uid=user04,cn=users,dc=example,dc=com"

A company has two sites with containers created for each. The following command
can be used to transfer a user from the container for the site "Hamburg" to the
container for the site "Bremen":

.. code-block::

   $ univention-directory-manager users/user move \
   > --dn "uid=user03,cn=hamburg,cn=users,dc=example,dc=com" \
   > --position "cn=bremen,cn=users,dc=example,dc=com"

.. _central-udm-example-groups:

Groups
~~~~~~

Creating a group ``Example Users`` and adding the user ``user01`` to this group:

.. code-block::

   $ univention-directory-manager groups/group create \
   > --position "cn=groups,dc=example,dc=com" \
   > --set name="Example Users" \
   > --set users="uid=user01,cn=users,dc=example,dc=com"

Subsequent addition of the user ``user02`` to the existing group:

.. code-block::

   $ univention-directory-manager groups/group modify \
   > --dn "cn=Example Users,cn=groups,dc=example,dc=com" \
   > --append users="uid=user02,cn=users,dc=example,dc=com"

.. caution::

   A ``--set`` on the attribute ``users`` overwrites the list of group members
   in contrast to ``--append``.

Subsequent removal of the user ``user01`` from the group:

.. code-block::

   $ univention-directory-manager groups/group modify \
   > --dn "cn=Example Users,cn=groups,dc=example,dc=com" \
   > --remove users="uid=user01,cn=users,dc=example,dc=com"

.. _central-udm-example-cn-policies:

Container / Policies
~~~~~~~~~~~~~~~~~~~~

This call creates a container ``cn=Bremen`` beneath the standard container
``cn=computers`` for the computers at the "Bremen" site. The additional option
``computerPath`` also registers this container directly as the standard
container for computer objects (see :ref:`central-cn-and-ous`):

.. code-block::

   $ univention-directory-manager container/cn create \
   > --position "cn=computers,dc=example,dc=com" \
   > --set name="bremen" \
   > --set computerPath=1

This command creates a disk quota policy with soft and hard limits and the name
*Default quota*:

.. code-block::

   $ univention-directory-manager policies/share_userquota create \
   > --position "cn=policies,dc=example,dc=com" \
   > --set name="Default quota" \
   > --set softLimitSpace=5GB \
   > --set hardLimitSpace=10GB

This policy is now linked to the user container ``cn=users``:

.. code-block::

   $ univention-directory-manager container/cn modify \
   > --dn "cn=users,dc=example,dc=com" \
   > --policy-reference "cn=Default quota,cn=policies,dc=example,dc=com"

Creating a |UCSUCR| policy with which the storage time for log files can be set
to one year. One space is used to separate the name and value of the variable:

.. code-block::

   $ univention-directory-manager policies/registry create \
   > --position "cn=config-registry,cn=policies,dc=example,dc=com" \
   > --set name="default UCR settings" \
   > --set registry="logrotate/rotate/count 52"

This command can be used to attach an additional value to the created policy:

.. code-block::

   $ univention-directory-manager policies/registry modify \
   > --dn "cn=default UCR settings,cn=config-registry,cn=policies,dc=example,dc=com" \
   > --append registry='"logrotate/compress" "no"'

.. _central-udm-example-cn-computers:

Computers
~~~~~~~~~

In the following example, a Windows client is created. If this client joins the
Samba domain at a later point in time (see :ref:`windows-domain-join`), this
computer account is then automatically used:

.. code-block::

   $ univention-directory-manager computers/windows create \
   > --position "cn=computers,dc=example,dc=com" \
   > --set name=WinClient01 \
   > --set mac=aa:bb:cc:aa:bb:cc \
   > --set ip=192.0.2.10

.. _central-udm-example-shares:

Shares
~~~~~~

The following command creates a share *Documentation* on the server
*fileserver.example.com*. As long as :file:`/var/shares/documentation/` does not
yet exist on the server, it is also created automatically:

.. code-block::

   $ univention-directory-manager shares/share create \
   > --position "cn=shares,dc=example,dc=com" \
   > --set name="Documentation" \
   > --set host="fileserver.example.com" \
   > --set path="/var/shares/documentation"

.. _central-udm-example-printer:

Printers
~~~~~~~~

Creating a printer share *LaserPrinter01* on the print server
*printserver.example.com*. The properties of the printer are specified in the
PPD file, the name of which is given relative to the directory
:file:`/usr/share/ppd/`. The connected printer is network-compatible and is
connected via the IPP protocol.

.. code-block::

   $ univention-directory-manager shares/printer create \
   > --position "cn=printers,dc=example,dc=com" \
   > --set name="LaserPrinter01"  \
   > --set spoolHost="printserver.example.com" \
   > --set uri="ipp:// 192.0.2.100" \
   > --set model="foomatic-rip/HP-Color_LaserJet_9500-Postscript.ppd" \
   > --set location="Head office" \
   > --set producer="producer: cn=HP,cn=cups,cn=univention,dc=example,dc=com"

.. note::

   There must be a blank space between the print protocol and the URL target
   path in the parameter ``uri``. A list of the print protocols can be found in
   :ref:`print-shares`.

Printers can be grouped in a printer group for simpler administration. Further
information on printer groups can be found in :ref:`printer-groups`.

.. code-block::

   $ univention-directory-manager shares/printergroup create \
   > --set name=LaserPrinters \
   > --set spoolHost="printserver.example.com" \
   > --append groupMember=LaserPrinter01 \
   > --append groupMember=LaserPrinter02

.. _central-udm-example-dnsdhcp:

DNS/DHCP
~~~~~~~~

To configure an IP assignment via DHCP, a DHCP computer entry must be registered
for the MAC address. Further information on DHCP can be found in
:ref:`module-dhcp-dhcp`.

.. code-block::

   $ univention-directory-manager dhcp/host create \
   > --superordinate "cn=example.com,cn=dhcp,dc=example,dc=com" \
   > --set host="Client222" \
   > --set fixedaddress="192.0.2.110" \
   > --set hwaddress="ethernet 00:11:22:33:44:55"

If it should be possible for a computer name to be resolved via DNS, the
following commands can be used to configure a forward (host record) and reverse
resolution (PTR record).

.. code-block::

   $ univention-directory-manager dns/host_record create \
   > --superordinate "zoneName=example.com,cn=dns,dc=example,dc=com" \
   > --set name="Client222" \
   > --set a="192.0.2.110"

   $ univention-directory-manager dns/ptr_record create \
   > --superordinate "zoneName=0.168.192.in-addr.arpa,cn=dns,dc=example,dc=com" \
   > --set address="110" \
   > --set ptr_record="Client222.example.com."

Further information on DNS can be found in :ref:`networks-dns`.

.. _central-udm-example-extended-attr:

Extended attributes
~~~~~~~~~~~~~~~~~~~

Extended attributes can be used to expand the functional scope of UMC modules,
see :ref:`central-extended-attrs`. In the following example, a new attribute is
added, where the car license number of the company car can be saved for each
user. The values are managed in the object class ``univentionFreeAttributes``
created specially for this purpose:

.. code-block::

   $ univention-directory-manager settings/extended_attribute create \
   > --position "cn=custom attributes,cn=univention,dc=example,dc=com" \
   > --set name="CarLicense" \
   > --set module="users/user" \
   > --set ldapMapping="univentionFreeAttribute1" \
   > --set objectClass="univentionFreeAttributes" \
   > --set longDescription="License plate number of the company car" \
   > --set tabName="Company car" \
   > --set multivalue=0 \
   > --set syntax="string" \
   > --set shortDescription="Car license"

