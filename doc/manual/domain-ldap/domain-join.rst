.. _domain-join:

Joining domains
===============

.. highlight:: console

A UCS, Ubuntu or Windows system must join the domain after installation.

In addition to UCS, Ubuntu and macOS, arbitrary Unix systems can be integrated
into the domain. This is described in :cite:t:`ext-doc-domain`.

.. _linux-domain-join:

How UCS systems join domains
----------------------------

There are three possibilities for a UCS system to join an existing domain:

* Directly after installation in the Univention Installer, see
  :ref:`installation-domain-settings-join-ucs-domain`.

* Subsequently with the command :command:`univention-join`, see
  :ref:`domain-ldap-subsequent-domain-joins-with-univention-join`.

* Using the UMC module :guilabel:`Domain join`, see
  :ref:`linux-domain-join-umc`.


The |UCSPRIMARYDN| should always be installed at the most up-to-date release
stand of the domains, as problems can arise with an outdated |UCSPRIMARYDN| when
a system using the current version joins.

When a computer joins, a computer account is created, the SSL
certificates are synchronized and an LDAP copy is initiated if
necessary. The *join scripts* are also run at the
end of the join process. These register further objects, etc., in the
directory service using the software packages installed on the system
(see :ref:`domain-ldap-joinscripts`).

The joining of the domain is registered on the client side in the
:file:`/var/log/univention/join.log` log file, which can be used for reference
in error analysis. Actions run on the |UCSPRIMARYDN| are stored in the
:file:`/home/<Join-Account>/.univention-server-join.log` log file.

The joining process can be repeated at any time. Systems may even be required to
rejoin following certain administrative steps (such as changes to important
system features on the |UCSPRIMARYDN|).

.. _domain-ldap-subsequent-domain-joins-with-univention-join:

Subsequent domain joins with *univention-join*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. program:: univention-join

:command:`univention-join` retrieves a number of essential parameters
interactively; however, it can also be configured using a number of parameters:

.. option:: -dcname <HOSTNAME>

   The |UCSPRIMARYDN| is usually detected via a DNS request. If that is not
   possible (e.g., a |UCSREPLICADN| server with a different DNS domain is set to
   join), the computer name of the |UCSPRIMARYDN| can also be entered directly
   using the ``-dcname HOSTNAME`` parameter. The computer name must then be
   entered as a fully qualified name, e.g., ``primary.company.com``.

.. option:: -dcaccount <ACCOUNTNAME>

   A user account which is authorized to add systems to the UCS domains is
   called a join account. By default, this is the ``Administrator`` user or a
   member of the two groups ``Domain Admins`` and ``DC Backup Hosts``. The join
   account can be assigned using the ``-dcaccount ACCOUNTNAME`` parameter.

.. option:: -dcpwd <FILE>

   The password can be set using the ``-dcpwd FILE`` parameter. The password is
   then read out of the specified file.

.. option:: -verbose

   The ``-verbose`` parameter is used to add additional debug output to the log
   files, which simplify the analysis in case of errors.

.. _linux-domain-join-umc:

Joining domains via |UCSUMC| module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A domain join can also be carried out web based via the UMC module
:guilabel:`Domain join`. As the *Administrator* user does not yet exist on a
system which has yet to join the domain, the login to the module is done as user
``root``.

As for the :ref:`domain joining procedure via the command line
<domain-ldap-subsequent-domain-joins-with-univention-join>`, username and
password of a user account authorized to add computers to a domain must be
entered in the resulting dialogue. Likewise, the |UCSPRIMARYDN| will be
determined automatically via a DNS request, but can also be entered manually.

The :guilabel:`Rejoin` option can be used to repeat the domain join at any time.

.. _domain-ldap-joinscripts:

Join scripts / Unjoin scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Join scripts* are run during the domain join. Examples for changes made by
join scripts are the registration of a print server in the domain or the
adaptation of DNS entries. Join scripts are components of the individual
software packages. In the same way, there are also *unjoin scripts*, which can
reset these changes following deinstallation of software components.

Join scripts are stored in the :file:`/usr/lib/univention-install/` directory
and unjoin scripts in :file:`/usr/lib/univention-uninstall/`. Each join/unjoin
script has a version. An example: A package has already been installed and the
join script already run. The new version of the package now requires additional
changes and the version number of the join script is increased.

The :command:`univention-check-join-status` command can be used to check whether
join/unjoin scripts need to be run (either because they have yet to be run or an
older version was run).

.. _domain-ldap-joinscripts-execlater:

Subsequent running of join scripts
""""""""""""""""""""""""""""""""""

If there are join/unjoin scripts on a system which have not yet been run or
which can only be run for an older version, a warning message is shown upon
opening a UMC module.

Join scripts that have not been run can be executed via the UMC module
:guilabel:`Domain join` by clicking on the menu entry :guilabel:`Execute all
pending join scripts`.

The :command:`univention-run-join-scripts` command is used to run all of the
join/unjoin scripts installed on a system. The scripts check automatically
whether they have already been executed.

The name of the join/unjoin script and the output of the script are also
recorded in :file:`/var/log/univention/join.log`.

If :command:`univention-run-join-scripts` is run on another system role than the
|UCSPRIMARYDN|, the user will be asked to input a username and password. This
can be performed on the |UCSPRIMARYDN| via the ``--ask-pass`` option.

.. _windows-domain-join:

Windows domain joins
--------------------

The procedure for joining a Windows system to a UCS domain made available via
Samba is now described as an example for Windows 10 and Windows 2012 / 2016 /
2019. The process is similar for other Windows versions. In addition to the
client versions, Windows server systems can also join the domain. Windows
servers join the domain as member servers; joining a Windows systems as a domain
controller is not supported. Further information can be found in
:ref:`windows-services-for-windows`.

Only domain-compatible Windows versions can join the UCS domain, i.e.,
it is not possible for the Home versions of Windows to join a domain.

A host account is created for the Windows client automatically when it joins the
domain (see :ref:`computers-hostaccounts`). Information concerning MAC and IP
addresses, the network, DHCP or DNS can be configured via UMC modules prior to
or after joining the domain.

Domain joining is usually performed with the local Administrator account on the
Windows system.

Joining the domain takes some time and the process must not be canceled
prematurely. After successful joining a small window appears with the message
*Welcome to the domain <your domain name>*. This should be confirmed with
:guilabel:`OK`. The computer must then be restarted for the changes to take
effect.

Domain names must be limited to 13 characters as they are otherwise truncated at
the Windows client and this can lead to sign in errors.

For a domain join against a domain controller based on Samba/AD, the DNS
configuration of the client must be set up in such a way that DNS entries from
the DNS zone of the UCS domain can also be resolved. In addition, the time on
the client system must also be synchronized with the time on the domain
controller.

.. _domain-ldap-windows-10:

Windows 10
~~~~~~~~~~

The joining of domains is only possible with the Pro and Enterprise editions of
Windows 10.

The control panel can be reached via the search field :guilabel:`Search the web
and Windows`, which can be found in the start bar. Under :menuselection:`System
and Security --> System` it must be clicked on :menuselection:`Change settings
--> Change`.

The :guilabel:`Domain` option field must be ticked and the name of the domain
must be entered in the input field for the domain join. The full domain name
should be used, e.g. ``mydomain.intranet``. After clicking on the :guilabel:`OK`
button, the username of a domain administrator must be entered in the input
field :guilabel:`Username`, by default this is ``Administrator``. The password
of the domain administrator has to be entered in the input field
:guilabel:`Password`. Finally, the process for joining the domain can then be
started by clicking on :guilabel:`OK`.

.. _domain-ldap-win-2012:

Windows Server 2012 / 2016 / 2019
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The control panel can be reached by moving the cursor to the bottom right-hand
corner of the screen. The *Control Panel* can then be searched for under
:menuselection:`Search --> Apps`. :menuselection:`Change settings --> Network
ID` must be clicked on under :menuselection:`System and Security --> System`.

The *Domain* option field must be ticked and the name of the Samba domain
entered in the input field for the domain join. After clicking on the
:guilabel:`OK` button, the username ``Administrator`` must be entered in the
input field *Name* and the password from :samp:`uid=Administrator,cn=users,{LDAP
base DN}` transferred to the *Password* input field. The process for joining the
domain can then be started by clicking on :guilabel:`OK`.

.. _ubuntu-domain-join:

Ubuntu domain joins
-------------------

Univention provides the :program:`Univention Domain Join Assistant` to integrate
Ubuntu clients into a UCS domain. Documentation and installation instructions
are available at `Github <github-univention-domain-join_>`_.

.. _macos-domain-join:

macOS domain joins
------------------

UCS supports domain joins of macOS clients into a UCS environment using
Samba/AD. This documentation refers to macOS 10.8.2.

The domain join can be performed using the system preferences menu or
the :command:`dsconfigad` command line tool.

After the domain join it is possible to automatically mount CIFS shares
to subfolders in :file:`/Volumes` when logging in with a
domain user. For that, the following line has to be added to the file
:file:`/etc/auto_master`:

::

   /Volumes	auto_custom


In addition, the file :file:`/etc/auto_custom` needs to be created and the shares
which should be mounted have to be listed in it in the following way:

::

   <SUBFOLDER_NAME>    -fstype=smbfs    ://<FQDN>/<SHARE_NAME>


Note that the automatically mounted shares are not displayed in the finder's sidebar.

.. _macos-domain-join-gui:

Domain join using the system preferences GUI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the System Preferences via the :guilabel:`Users & Groups` entry, the
:guilabel:`Login menu` can be reached. After authenticating by clicking on the
lock in the lower left corner and providing credentials of a local
*Administrator* account, the :guilabel:`Network Account Server: Join` button
needs to be clicked. From that menu it is possible to open the *Directory
Utility*.

.. _domain-ldap-join-osx:

.. figure:: /images/macosx-bind.*
   :alt: Domain join of a macOS system

   Domain join of a macOS system

In the advanced options section, the option *Create mobile account at login*
should be activated. A mobile account has the advantage that, when the domain is
not available, the user can log into the macOS system with the same account used
for logging into the domain.

After filling in the domain name in the field *Active Directory Domain* and the
hostname of the macOS client in the field *Computer ID*, the join process is
initiated after clicking the button :guilabel:`Bind...`. The username and
password of an account in the ``Domain Admins`` group needs to be entered, e.g.,
``Administrator``.

.. _macos-domain-join-cli:

Domain join on the command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The domain join can also be performed on the command line using
:command:`dsconfigad`:

.. code-block::

   $ dsconfigad -a <MAC HOSTNAME> \
   > -domain <FQDN> \
   > -ou "CN=Computers,<LDAP base DN>" \
   > -u <Domain Administrator> \
   > -mobile enable

Additional configuration options are available through :command:`dsconfigad
-help`.
