.. _chap-ldap:
.. _ldap-general:

***************************************************
Lightweight Directory Access Protocol (LDAP) in UCS
***************************************************

An LDAP server provides authenticated and controlled access to directory objects
over the network. LDAP objects consist of a collection of attributes which
conform to so called LDAP schemata. An in depth documentation of LDAP is beyond
the scope of this document. Other resources cover this topic exhaustively, for
example `<http://www.zytrax.com/books/ldap/>`_ or the manual pages
:manpage:`slapd.conf.5` and :manpage:`slapd.access.5`.

At least it should be noted that OpenLDAP offers two fundamentally different
tool sets for direct access or modification of LDAP data:

#. The :samp:`slap{*}` commands (:command:`slapcat`, etc.) are very low level,
   operating directly on the LDAP back end data and should only be used in rare
   cases, usually with the LDAP server not running.

#. The :samp:`ldap{*}` commands (:command:`ldapsearch`, etc.) on the other hand
   are the proper way to perform LDAP operations from the command line and their
   functionality can equivalently be used from all major programming languages.

On top of the raw LDAP layer, the |UCSUDM| offers an object model on a higher
level, featuring advanced object semantics (see :ref:`chap-udm`). That level is
usually appropriate for app developers, which should be considered before
venturing down to the level of direct LDAP operations. On the other hand, for
the development of new UDM extensions it is important to understand some of the
essential concepts of LDAP as used in UCS.

One essential trait of LDAP as used in UCS, is the strict enforcement of LDAP
schemata. An LDAP server refuses to start if an unknown LDAP attribute is
referenced either in the configuration or in the back end data. This makes it
critically important to install schemata on all systems. To simplify this task
UCS features a built-in mechanism for automatic schema replication to all UCS
hosted LDAP servers in the UCS domain (see :ref:`chap-listener`). The schema
replication mechanism is triggered by installation of a new schema extension
package on the |UCSPRIMARYDN|. For redundancy it is strongly recommended to
install schema extension packages also on each |UCSBACKUPDN|. This way, a
|UCSBACKUPDN| can replace a |UCSPRIMARYDN| in case the |UCSPRIMARYDN| needs to
be replaced for some reason. To simplify these tasks even further, UCS offers
methods to register new LDAP schemata and associated LDAP ACLs from any UCS
system.

.. _settings-ldapschema:

Packaging LDAP Schema Extensions
================================

For some purposes, for example for app installation, it is convenient to be able
to register a new LDAP schema extension from any system in the UCS domain. For
this purpose, the schema extension can be stored as a special type of UDM
object. The module responsible for this type of objects is called
``settings/ldapschema``. As these objects are replicated throughout the UCS
domain, the |UCSPRIMARYDN| and |UCSBACKUPDN| systems listen for modifications of
these objects and integrate them into their local LDAP schema directory. As noted
above, this simplifies the task of keeping the schema on the |UCSBACKUPDN|
systems up to date with those on the |UCSPRIMARYDN|.

The commands to create the LDAP schema extension objects in UDM may be put into
any join script (see :ref:`chap-join`). A LDAP schema extension object is
created by using the UDM command line interface
:command:`univention-directory-manager` or its alias :command:`udm`. LDAP schema
extension objects can be stored anywhere in the LDAP directory, but the
recommended location would be ``cn=ldapschema,cn=univention,`` below the LDAP
base. Since the join script creating the attribute may be called on multiple
hosts, it is a good idea to add the ``--ignore_exists`` option, which suppresses
the error exit code in case the object already exists in LDAP.

The UDM module ``settings/ldapschema`` requires several parameters:

``name`` (required)
   Name of the schema extension.

``data`` (required)
   The actual schema data in ``bzip2`` and ``base64`` encoded format.

``filename`` (required)
   The file name the schema should be written to on |UCSPRIMARYDN| and
   |UCSBACKUPDN|. The filename must not contain any path elements.

``package`` (required)
   Name of the Debian package which creates the object.

``packageversion`` (required)
   Version of the Debian package which creates the object. For object
   modifications the version number needs to increase unless the package
   name is modified as well.

``appidentifier`` (optional)
   The identifier of the app which creates the object. This is important
   to indicate that the object is required as long as the app is
   installed anywhere in the UCS domain. Defaults to
   ``string``.

``active`` (internal)
   A boolean flag used internally by the |UCSPRIMARYDN| to signal
   availability of the schema extension (default:
   ``FALSE``).

Since many of these parameters are determined automatically by the
:ref:`ucs_registerLDAPExtension <join-ucs-register-ldap-extension>` shell
library function, it is recommended to use the shell library function to create
these objects (see :ref:`join-libraries-shell`).

.. code-block:: bash
   :caption: Schema registration in join script
   :name: join-register-schema

   export UNIVENTION_APP_IDENTIFIER="appID-appVersion" ## example
   . /usr/share/univention-lib/ldap.sh

   ucs_registerLDAPExtension "$@" \
     --schema /path/to/appschemaextension.schema


.. _settings-ldapacl:

Packaging LDAP ACL Extensions
=============================

For some purposes, for example for app installation, it is convenient to be
able to register a new LDAP ACL extension from any system in the UCS
domain. For this purpose, the UCR template for an ACL extension can be
stored as a special type of UDM object. The module responsible for this
type of objects is called ``settings/ldapacl``. As these objects are
replicated throughout the UCS domain, the |UCSPRIMARYDN|, |UCSBACKUPDN| and
|UCSREPLICADN| systems listen for modifications on these objects and
integrate them into the local LDAP ACL UCR template directory. This
simplifies the task of keeping the LDAP ACLs on the |UCSBACKUPDN| systems
up to date with those on the |UCSPRIMARYDN|.

The commands to create the LDAP ACL extension objects in UDM may be put into any
join script (see :ref:`chap-join`). A LDAP ACL extension object is created by
using the UDM command line interface :command:`univention-directory-manager` or
its alias :command:`udm`. LDAP ACL extension objects can be stored anywhere in
the LDAP directory, but the recommended location would be
``cn=ldapacl,cn=univention,`` below the LDAP base. Since the join script
creating the attribute may be called on multiple hosts, it is a good idea to add
the ``--ignore_exists`` option, which suppresses the error exit code in case the
object already exists in LDAP.

The UDM module ``settings/ldapacl`` requires several parameters:

``name`` (required)
   Name of the ACL extension.

``data`` (required)
   The actual ACL UCR template data in ``bzip2`` and ``base64`` encoded format.

``filename`` (required)
   The filename the ACL UCR template data should be written to on
   |UCSPRIMARYDN|, |UCSBACKUPDN| and |UCSREPLICADN|. The filename must not
   contain any path elements.

``package`` (required)
   Name of the Debian package which creates the object.

``packageversion`` (required)
   Version of the Debian package which creates the object. For object
   modifications the version number needs to increase unless the package
   name is modified as well.

``appidentifier`` (optional)
   The identifier of the app which creates the object. This is important
   to indicate that the object is required as long as the app is
   installed anywhere in the UCS domain. Defaults to
   ``string``.

``ucsversionstart`` (optional)
   Minimal required UCS version. The UCR template for the ACL is only
   activated by systems with a version higher than or equal to this.

``ucsversionend`` (optional)
   Maximal required UCS version. The UCR template for the ACL is only
   activated by systems with a version lower or equal than this. To
   specify validity for the whole 4.1-x release range a value like
   ``4.1-99`` may be used.

``active`` (internal)
   A boolean flag used internally by the |UCSPRIMARYDN| to signal
   availability of the ACL extension on the |UCSPRIMARYDN| (default:
   ``FALSE``).

Since many of these parameters are determined automatically by the
:ref:`ucs_registerLDAPExtension <join-ucs-register-ldap-extension>` shell
library function, it is recommended to use the shell library function to create
these objects (see :ref:`join-libraries-shell`).

.. code-block:: bash
   :caption: LDAP ACL registration in join script
   :name: join-register-acl

   export UNIVENTION_APP_IDENTIFIER="appID-appVersion" ## example
   . /usr/share/univention-lib/ldap.sh

   ucs_registerLDAPExtension "$@" \
     --acl /path/to/appaclextension.acl


.. _join-secret:

LDAP secrets
============

.. index::
   single: domain join; domain credentials

The credentials for different UCS domain accounts are stored in plain-text files
on some UCS systems. The files are named :file:`/etc/{*}.secret`. They are owned
by the user ``root`` and allow read-access for different groups.

:file:`/etc/ldap.secret` for :samp:`cn=admin,{$ldap_base}`
   This account has full write access to all LDAP entries. The file is
   only available on |UCSPRIMARYDN| and |UCSBACKUPDN| systems and is owned
   by the group ``DC Backup Hosts``.

:file:`/etc/machine.secret` for :samp:`{$ldap_hostdn}`
   Each host uses its account to get at least read-access to LDAP. Directory
   Nodes, for example Domain controllers, in the container
   :samp:`cn=dc,cn=computers,{$ldap_base}` get additional rights to access LDAP
   attributes. The file is available on all joined system roles and is readable
   only by the local ``root`` user and group.

During package installation, only the maintainer scripts (see
:ref:`deb-scripts`) on |UCSPRIMARYDN| and |UCSBACKUPDN| can use their ``root``
permission to directly read :file:`/etc/ldap.secret`. Thus only on those roles,
the join scripts get automatically executed when the package is installed. On
all other system roles, the join scripts need to be executed manually. This can
either be done through the *UMC Join module* or through the command line tool
:command:`univention-run-join-scripts`. Both methods require appropriate
credentials.

.. _join-secret-change:

Password change
---------------

.. index::
   single: domain join; domain credentials
   single: domain join; machine credential change
   see: server password change; domain join

To reconfirm the trust relation between UCS systems, computers need to regularly
change the password associated with the machine account. This is controlled
through the |UCSUCRV| :envvar:`server/password/change`. For UCS servers this is
evaluated by the script
:file:`/usr/lib/univention-server/server_password_change`, which is invoked
nightly at 01:00 by :manpage:`cron.8`. The interval is controlled through a
second |UCSUCRV| :envvar:`server/password/interval`, which defaults to 21 days.

The password is stored in the plain text file :file:`/etc/machine.secret`. Many
long running services read these credentials only on startup, which breaks when
the password is changed while they are still running. Therefore, UCS provides a
mechanism to invoke arbitrary commands, when the machine password is changed.
This can be used for example to restart specific services.

Hook scripts should be placed in the directory
:file:`/usr/lib/univention-server/server_password_change.d/`. The name must
consist of only digits, upper and lower ASCII characters, hyphens and
underscores. The file must be executable and is called through
:manpage:`run-parts.8`. It receives one argument, which is used to distinguish
three phases:

.. _join-server-password-procedure:

#. Each script will be called with the argument ``prechange`` before the
   password is changed. If any script terminates with an exit status unequal
   zero, the change is aborted.

#. A new password is generated locally using :manpage:`makepasswd.1`. It is
   changed in the Univention directory service through UDM and stored in
   :file:`/etc/machine.secret`. The old password is logged in
   :file:`/etc/machine.secret.old`.


   If anything goes wrong in this step, the change is aborted and the changes
   need to be rolled back.

   .. PMH: hard coded to 8 characters Bug #31281

#. All hook scripts are called again.

   * If the password change was successful, ``postchange`` gets passed to the
     hook scripts. This should complete any change prepared in the ``prechange``
     phase.

   * If the password change failed for any reason, all hook scripts are called
     with the argument ``nochange``. This should undo any action already done in
     the ``prechange`` phase.

Install this file to :file:`/usr/lib/univention-server/server_password_change.d/`.

.. code-block:: bash
   :caption: Server password change example
   :name: join-server-password-example

   #!/bin/sh
   case "$1" in
   prechange)
       # nothing to do before the password is changed
       exit 0
       ;;
   nochange)
       # nothing to do after a failed password change
       exit 0
       ;;
   postchange)
       # restart daemon after password was changed
       deb-systemd-invoke restart my-daemon
       ;;
   esac


init-scripts should only be invoked indirectly through
:manpage:`deb-systemd-invoke.1p`. This is required for :command:`chroot`
environments and allows the policy layer to control starting and stopping in
certain special situations like during an system upgrade.

.. PMH: we need to use it too Bug #18497

