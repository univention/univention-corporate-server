.. _chap-misc:

*************
Miscellaneous
*************

.. _misc-database:

Databases
=========

.. index::
   single: database

UCS ships with two major database management systems, which are used for UCS
internal purposes, but can also be used for custom additions.

.. _misc-postgresql:

PostgreSQL
----------

.. index::
   single: database; postgresql

UCS uses PostgreSQL by default for its package tracking database, which collects
the state and versions of packages installed on all systems of the domain.

.. _misc-mysql:

MariaDB
-------

.. index::
   single: database; mariadb
   single: database; mysql

By default the MariaDB root password is set to ``___``. Debian provides the
:program:`dbconfig` package, which can be used to create and modify additional
databases from maintainer scripts.

.. _misc-ucslint:

UCS lint
========

.. index::
   single: packaging; check for errors

Use :command:`ucslint` to find packaging issues.

For each issue one or more lines are printed. The first line per issue always
contains several fields separated by ``:``:

:samp:`{severity}:{module-id}-{test-id}[:{filename}[:{line-number}[:{column-number}]]]:{message}`

For some issues extra context data is printed on the following lines, which are
indented with space characters. All other lines start with a letter specifying
the severity:

``E``
   Error: Missing data, conflicting information, real bugs.

``W``
   Warning: Possible bug, but might be okay in some situations.

``I``
   Informational: found some issue, which needs further investigation.

``S``
   Style: There might be some better less error prone way.

The severities are ordered by importance. By default :command:`ucslint` only
aborts on errors, but this can be overwritten using the
``--exitcode-categories`` argument followed by a subset of the characters
``EWIS``.

After the severity an identifier follows, which uniquely identifies the module
and the test. The module is given as four digits, which is followed by a dash
and the number of the test in that module. Currently the following modules
exist:

``0001-CheckJoinScript``
   Checks join file issues

``0002-CopyPasteErrors``
   Checks for copy & paste error from example files

``0004-CheckUCR``
   Checks UCR info files

``0006-CheckPostinst``
   Checks Debian maintainer scripts

``0007-Changelog``
   Checks :file:`debian/changelog` file for conformance with Univention rules

``0008-Translations``
   Checks translation files for completeness and errors

``0009-Python``
   Checks Python files for common errors

``0010-Copyright``
   Checks for Univention copyright

``0011-Control``
   Checks :file:`debian/control` file for errors

``0013-bashism``
   Checks files using :file:`/bin/sh` for BASH constructs

``0014-Depends``
   Checks files for missing runtime dependencies on UCS packages

``0015-FuzzyNames``
   Checks for spelling of Univention

``0016-Deprecated``
   Checks files for usage of deprecated functions

``0017-Shell``
   Checks shell scripts for quoting errors

``0018-Debian``
   Checks for Debian packaging issues

``0020-flake8``
   Checks Python scripts for :command:`flake8` issues

The module and test number may be optionally followed by a filename, line
number in that file, and column number in that line, where the issue was found.
After that a message is printed, which describes the issue in more detail.

Since :command:`ucslint` is very Univention centric, many of its tests return
false positives for software packages by other parties. Therefore, many tests
need to be disables. For this the file :file:`debian/ucslint.overrides` can be
created with list of modules and test to be ignored. Without specifying the
optional filename, line number and column number, the test is globally disabled
for all files.

.. _misc-lib:

Function libraries
==================

.. index::
   single: packaging; library functions

The source package :program:`univention-lib` provides the binary packages
:program:`shell-univention-lib`, :program:`python3-univention-lib` and
:program:`python-univention-lib`, which contain common library functions usable
in shell or Python programs.

.. PMH: poorly documented and of questionale code quality

.. _misc-lib-sh:

:program:`shell-univention-lib`
-------------------------------

This package (and several others) provides shell libraries in
:file:`/usr/share/univention-lib/`, which can be used in shell scripts.

:file:`/usr/share/univention-lib/admember.sh`
   This file contains some helpers to test for and to manage hosts in AD member
   mode.

:file:`/usr/share/univention-lib/backup.sh`
   This file contains code to remove old backup files from
   :file:`/var/univention-backup/`.

:file:`/usr/share/univention-lib/base.sh`
   This file contains some helpers to create log files, handle unjoin scripts
   (see :ref:`join-unjoin`) or query the network configuration.

:file:`/usr/share/univention-lib/join.sh`
   This file is provided by the package :program:`univention-join`. It is used
   by by Debian maintainer scripts to register and call join scripts. See
   :ref:`join-libraries-shell` for further details.

:file:`/usr/share/univention-lib/ldap.sh`
   This file contains some helpers to query data from LDAP, register and
   un-register service entries, LDAP schema and LDAP ACL extensions.

:file:`/usr/share/univention-lib/samba.sh`
   This file contains a helper to check is Samba4 is used.

:file:`/usr/share/univention-lib/ucr.sh`
   This file is provided by the package :program:`univention-config`. It
   contains some helpers to handle boolean |UCSUCRV|\ s and handle UCR files on
   package removal. See :ref:`ucr-usage-shell` for further details.

:file:`/usr/share/univention-lib/umc.sh`
   This file contains some helpers to handle UMC (see :ref:`chap-umc`) related
   tasks.

:file:`/usr/share/univention-lib/all.sh`
   This is a convenient library, which just includes all libraries mentioned
   above.

.. _misc-lib-python:

:program:`python-univention-lib`
--------------------------------

This package provides several Python libraries located in the module
:program:`univention.lib`.

:program:`univention.lib.admember`
   This module contains functions to test for and to manage hosts in AD member
   mode.

:program:`univention.lib.atjobs`
   This module contains functions to handle :command:`at`-jobs.

   .. PMH: Bug #27670

:program:`univention.lib.fstab`
   This module provides some functions for handling the file :file:`/etc/fstab`.

:program:`univention.lib.i18n`
   This module provides some classes to handle texts and their translations.

:program:`univention.lib.ldap_extension`
   This module provides some helper functions internally used to register LDAP
   extension as described in :ref:`join-libraries-shell`.

:program:`univention.lib.listenerSharePath`
   This module provides some helper functions internally used by the Directory
   Listener module handling file shares.

:program:`univention.lib.locking`
   This module provides some functions to implement mutual exclusion using file
   objects as locking objects.

   .. PMH: this should be re-witten using a Python context manager

:program:`univention.lib.misc`
   This module provides miscellaneous functions to query the set of configured
   LDAP servers, localized domain user names, and other functions.

:program:`univention.lib.package_manager`
   This module provides some wrappers for :command:`dpkg` and :program:`APT`,
   which add functions for progress reporting.

:program:`univention.lib.s4`
   This module provides some well known SIDs and RIDs.

:program:`univention.lib.ucrLogrotate`
   This module provides some helper functions internally used for parsing the
   |UCSUCRV|\ s related to :manpage:`logrotate.8`.

:program:`univention.lib.ucs`
   This module provides the class ``UCS_Version`` to more easily handle UCS
   version strings.

:program:`univention.lib.umc`
   This module provides the class ``Client`` to handle connections to remote UMC
   servers.

:program:`univention.lib.umc_module`
   This module provides some functions for handling icons.

.. _misc-acl:

Login access control
====================

Access control to services can be configured for individual services by setting
certain |UCSUCRV|\ s. Setting :samp:`auth/{SERVICE}/restrict` to ``true``
enables access control for that service. This will include the file
:file:`/etc/security/access-{SERVICE}.conf`, which contains the list of allowed
users and groups permitted to login to the service. Users and groups can be
added to that file by setting :samp:`auth/{SERVICE}/user/{USER}` and
:samp:`auth/{SERVICE}/group/{GROUP}` to ``true`` respectively.

.. _misc-nacl:

Network packet filter
=====================

.. PMH: Bug #24589 is outdated, see Bug #23577 for latest format

Firewall rules are setup by :program:`univention-firewall` and can be configured
through |UCSUCR| or by providing additional UCR templates.

.. _misc-nacl-ucr:

Filter rules by |UCSUCR|
------------------------

Besides predefined service definitions, Univention Firewall also allows the
implementation of package filter rules through |UCSUCR|. These rules are
included in :file:`/etc/security/packetfilter.d/` through a |UCSUCR| module.

Filter rules can be provided through packages or can be configured locally by
the administrator. Local rules have a higher priority and overwrite rules
provided by packages.

All |UCSUCR| settings for filter rules are entered in the following format:

Local filter rule
   :samp:`security/packetfilter/{protocol}/{>port(s)}{address}={policy}`

Package filter rule
   :samp:`security/packetfilter/package/{package}/{protocol}/{port(s)}/{address}={policy}`

The following values need to be filled in:

:samp:`{package}` (only for packaged rules)
   The name of the package providing the rule.

:samp:`{protocol}`
   Can be either ``tcp`` for server services using the *Transmission Control
   Protocol* or ``udp`` for services using the stateless *User Datagram Protocol*.

:samp:`{port}`; :samp:`min-port}:{max-port}`
   Ports can be defined either as a single number between 1 and 65535 or as a
   range separated by a colon: :samp:`{min-port}:{max-port}`

:samp:`{address}`
   This can be either ``ipv4`` for all IPv4 addresses, ``ipv6`` for all IPv6
   addresses, ``all`` for both IPv4 and IPv6 addresses, or any explicitly
   specified IPv4 or IPv6 address.

:samp:`{policy}`
   If a rule is registered as ``DROP``, then packets to this port will be
   silently discarded; ``REJECT`` can be used to send back an ICMP message
   ``port unreachable`` instead. Using ``ACCEPT`` explicitly allows such
   packets. (IPtables rules are executed until one rule applies; thus, if a
   package is accepted by a rule which is discarded by a later rule, then the
   rule for discarding the package does not become valid).

Filter rules can optionally be described by setting additional |UCSUCRV|\ s. For
each rule and language, an additional variable suffixed by :samp:`/{language}`
can be used to add a descriptive text.

Some examples:

.. code-block::
   :caption: Local firewall rules
   :name: misc-firewall

   security/packetfilter/tcp/2000/all=DROP
   security/packetfilter/tcp/2000/all/en=Drop all packets to TCP port 2000
   security/packetfilter/udp/500:600/all=ACCEPT
   security/packetfilter/udp/500:600/all/en=Accept UDP port 500 to 600


All package rules can be globally disabled by setting the |UCSUCRV|
:envvar:`security/packetfilter/use_packages` to ``false.``.

.. _misc-nacl-ipt:

Local filter rules through :command:`iptables` commands
-------------------------------------------------------

Besides the existing possibilities for settings through |UCSUCR|, there is also
the possibility of integrating user-defined enhanced configurations in
:file:`/etc/security/packetfilter.d/`, for example for realizing a firewall or
Network Address Translation. The enhancements should be realized in the form of
shell scripts which execute the corresponding :command:`iptables` for IPv4 and
:command:`ip6table` for IPv6 calls. For packages this is best done through using
a |UCSUCR| template as described in :ref:`ucr-file`.

Full documentation for IPTables can be found at the `netfilter/iptables project
<netfilter_>`_.

.. _misc-nacl-test:

Testing Univention Firewall settings
------------------------------------

Package filter settings should always be thoroughly tested. The network scanner
:command:`nmap`, which is integrated in |UCSUCS| as a standard feature, can be
used for testing the status of individual ports.

Since :program:`nmap` requires elevated privileges in the network stack, it should
be started as ``root`` user. A TCP port can be tested
with the following command: :samp:`nmap {HOSTNAME} -p {PORT(s)}`

A UDP port can be tested with the following command: :samp:`nmap {HOSTNAME} -sU -p {PORT(s)}`

.. code-block:: console
   :caption: Using :program:`nmap` for firewall port testing
   :name: misc-firewall-testing

   $ nmap 192.0.2.100 -p 400
   $ nmap 192.0.2.110 -sU -p 400-500

.. _ad-connection-custom-mappings:

Active Directory Connection custom mappings
===========================================

For general overview about the :program:`Active Directory Connection` app, see
:ref:`ad-connector-general` in :cite:t:`ucs-manual`.

It is possible to modify and append custom mappings. Administrators need to
create the file :file:`/etc/univention/connector/ad/localmapping.py`. Within
that file, they must implement the following function:

.. code-block:: python

   def mapping_hook(ad_mapping):
       return ad_mapping

The variable ``ad_mapping`` influences the mapping. The Active Directory
Connection app logs the resulting mapping to
:file:`/var/log/univention/connector-ad-mapping.log`, when the administrator
restarts |UCSADC|.
