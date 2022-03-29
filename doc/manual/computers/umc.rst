.. _computers-hostaccounts:

Management of computer accounts via |UCSUMC| module
===================================================

All UCS, Linux and Windows systems within a UCS domain each have a
computer domain account (also referred to as the host account) with
which the systems can authenticate themselves among each other and with
which they can access the LDAP directory.

The computer account is generally created automatically when the system
joins the UCS domain (see :ref:`domain-join`); however, the
computer account can also be added prior to the domain join.

The password for the computer account is generated automatically during
the domain join and saved in the
:file:`/etc/machine.secret` file. By default the
password consists of 20 characters (can be configured via the |UCSUCRV|
:envvar:`machine/password/length`). The password is regenerated
automatically at fixed intervals (default setting: 21 days; can be
configured using the |UCSUCRV|
:envvar:`server/password/interval`). Password rotation can also
be disabled using the variable :envvar:`server/password/change`.

There is an different computer object type for every system role.
Further information on the individual system roles can be found in
:ref:`system-roles`.

Computer accounts are managed in the UMC module
:guilabel:`Computers`.

By default a simplified wizard for creating a computer is shown, which
only requests the most important settings. All attributes can be shown
by clicking on :guilabel:`Advanced`. If there is a DNS forward
zone and/or a DNS reverse zone (see :ref:`networks-dns`) assigned to
the selected network object (see :ref:`networks-introduction`), a
host record and/or pointer record is automatically created for the host.
If there is a DHCP service configured for the network object and a MAC
address is configured, a DHCP host entry is created (see
:ref:`module-dhcp-dhcp`).

The simplified wizard can be disabled for all system roles by setting
the |UCSUCRV|
:envvar:`directory/manager/web/modules/computers/computer/wizard/disabled`
to ``true``.

.. _computers-create:

.. figure:: /images/computers_computer.*
   :alt: Creating a computer in the UMC module

   Creating a computer in the UMC module

.. _computers-create-advanced:

.. figure:: /images/computers_computer_advanced.*
   :alt: Advanced computer settings

   Advanced computer settings

.. _computers-management-table-general:

Computer management module - General tab
----------------------------------------

.. _computers-management-table-general-tab:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Description

   * - Name
     - The name for the host should be entered in this input field.

       To guarantee compatibility with different operating systems and services,
       computer names should only contain the lowercase letters *a* to *z*,
       numbers, hyphens and underscores. Umlauts and special characters are not
       permitted. The full stop is used as a separating mark between the
       individual components of a fully qualified domain name and must therefore
       not appear as part of the computer name. Computer names must begin with a
       letter.

       Microsoft Windows accepts computer names with a maximum of 13 characters,
       so as a rule computer names should be limited to 13 characters if there
       is any chance that Microsoft Windows will be used.

       After creation, the computer name can only be changed for the system
       roles *Windows Workstation/Server*, *macOS Client* and *IP client*.

   * - Description
     - Any description can be entered for the host in this input field.

   * - Inventory number
     - Inventory numbers for hosts can be stored here.

   * - Network
     - The host can be assigned to an existing network object. Information on the
       IP configuration can be found in :ref:`networks-introduction`.

   * - MAC address
     - The MAC address of the computer can be entered here, for example
       ``2e:44:56:3f:12:32``. If the computer is to receive a DHCP entry, the
       entry of the MAC address is essential.

   * - IP address
     - Fixed IP addresses for the host can be given here. Further information on
       the IP configuration can be found in :ref:`networks-introduction`.

       If a network was selected on the *General* tab, the IP address assigned
       to the host from the network will be shown here automatically.

       An IP address entered here (i.e. in the LDAP directory) can only be
       transferred to the host via DHCP. If no DHCP is being used, the IP
       address must be configured locally, see
       :ref:`hardware-network-configuration`.

       If the IP addresses entered for a host are changed without the DNS zones
       being changed, they are automatically changed in the computer object and
       - where they exist - in the DNS entries of the forward and reverse lookup
       zones. If the IP address of the host was entered at other places as
       well, these entries must be changed manually! For example, if the IP
       address was given in a DHCP boot policy instead of the name of the boot
       server, this IP address will need to be changed manually by editing the
       policy.

   * - Forward zone for DNS entry
     - The DNS forward zone in which the computer is entered. The zone is used
       for the resolution of the computer name in the assigned IP address.
       Further information on the IP configuration can be found in
       :ref:`networks-introduction`.

   * - Reverse zone for DNS entry
     - The DNS reverse zone in which the computer is entered. The zone is used
       to resolve the computer's IP address in a computer name. Further
       information on the IP configuration can be found in
       :ref:`networks-introduction`.

   * - DHCP service
     - If a computer is supposed to procure its IP address via DHCP, a DHCP
       service must be assigned here. Information on the IP configuration can be
       found in :ref:`networks-introduction`.

       During assignment, it must be ensured that the DHCP servers of the DHCP
       service object are responsible for the physical network.

       If a network is selected on the *General* tab an appropriate entry for
       the network will be added automatically. It can be adapted subsequently.

.. _computers-management-table-account:

Computer management module - Account tab
----------------------------------------

.. _computers-management-table-account-tab:

.. list-table:: *Account* tab (advanced settings)
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Description

   * - Password
     - The password for the computer account is usually automatically created
       and rotated. For special cases such as the integration of external
       systems it can also be explicitly configured in this field.

       The same password must then also be entered locally on the computer in
       the :file:`/etc/machine.secret` file.

   * - Primary group
     - The primary group of the host can be selected in this selection field.
       This is only necessary when they deviate from the automatically created
       default values. The default value for a |UCSPRIMARYDN| or |UCSBACKUPDN|
       is ``DC Backup Hosts``, for a |UCSREPLICADN| ``DC Slave Hosts`` and for
       |UCSMANAGEDNODE|\ s ``Computers``.

.. _computers-management-table-unix-account:

Computer management module - Unix account tab
---------------------------------------------

.. _computers-management-table-unix-account-tab:

.. list-table:: *Unix account* tab (advanced settings)
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Description

   * - Unix home directory (*)
     - A different input field for the host account can be entered here. The
       automatically created default value for the home directory is
       :file:`/dev/null`.

   * - Login shell
     - If a different login shell from the default value is to be used for the
       computer account, the login shell can be adapted manually in this input
       field. The automatically set default value assumes a login shell of
       :file:`/bin/sh`.

.. _computers-management-table-services:

Computer management module - Services tab
---------------------------------------------

.. _computers-management-table-services-tab:

.. list-table:: *Services* tab (advanced settings)
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Description

   * - Service
     - By means of a service object, applications or services can determine
       whether a service is available on a computer or generally in the domain.

.. note::

   The tab *Services* is only displayed on UCS server system roles.

.. _computers-management-deployment-services:

Computer management module - Deployment tab
-------------------------------------------

This *Deployment* tab is used for the Univention Net Installer, see `Extended
installation documentation
<https://docs.software-univention.de/installation-5.0.html>`_.

.. _computers-management-table-dns-alias:

Computer management module - DNS alias tab
------------------------------------------

.. _computers-management-table-dns-alias-tab:

.. list-table:: *DNS alias* tab (advanced settings)
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Description

   * - Zone for DNS Alias
     - If a zone entry for forward mapping has been set up for the host in the
       *Forward zone for DNS entry* field, the additional alias entries via
       which the host can be reached can be configured here.

.. _computers-management-table-groups:

Computer management module - Groups tab
---------------------------------------

The computer can be added into different groups in *Groups* tab.

.. _computers-management-table-options:

Computer management module - Options alias tab
----------------------------------------------

The *Options* tab allows to disable LDAP object classes for host objects. The
entry fields for attributes of disabled object classes are no longer shown. Not
all object classes can be modified subsequently.

.. _computers-management-table-options-tab:

.. list-table:: *(Options)* tab
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Description

   * - Kerberos principal
     - If this checkbox is not selected the host does not receive the
       ``krb5Principal`` and ``krb5KDCEntry`` object classes.

   * - POSIX account
     - If this checkbox is not selected the host does not receive the
       ``posixAccount`` object class.

   * - Samba account
     - If this checkbox is not selected the host does not receive the
       ``sambaSamAccount`` object class.

.. _computers-ubuntu:

Integration of Ubuntu clients
-----------------------------

Ubuntu clients can be managed in the UMC module
:guilabel:`Computers` with their own system role. The network
properties for DNS/DHCP can also be managed there.

The use of policies is not supported.

Some configuration adjustments need to be performed on Ubuntu systems; these are
documented in the `Extended domain services documentation
<https://docs.software-univention.de/domain-5.0.html>`_.
