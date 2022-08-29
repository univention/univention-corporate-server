.. _entry-point:

########################################################################
Univention Corporate Server - Extended Windows integration documentation
########################################################################

.. contents::

.. _samba:

****************************
Advanced Samba documentation
****************************

.. _samba-doc:

Operating Samba/AD as a read-only domain controller
===================================================

Active Directory offers an operating mode called *read-only
domain controller* (RODC) with the following properties:

* The data are only stored in read-only format. All write changes must be
  performed on another domain controller.

* Consequently, replication is only performed in one direction.

A comprehensive description can be found in the Microsoft TechNet Library
:cite:t:`technet-rodc`.

A Samba/AD domain controller can be operated in RODC mode (on a |UCSREPLICADN|
for example). Prior to the installation of :program:`univention-samba4`, the
|UCSUCRV| :envvar:`samba4/role` must be set to ``RODC``:

.. code-block:: console

   $ ucr set samba4/role=RODC
   $ univention-install univention-samba4
   $ univention-run-join-scripts

.. _ext-win-s4-deinstall:

Deinstallation of a Samba/AD domain controller
==============================================

The removal of an Samba/AD domain controller (Active Directory compatible domain
controller) is a far-reaching configuration step and should be prepared
thoroughly.

If the domain should continue to be provide Active Directory-compatible
services, the package :program:`univention-samba4` must remain installed on the
|UCSPRIMARYDN| or a |UCSBACKUPDN| system.

Before uninstalling the packages, the domain controller registration must be
removed from the Samba/AD database. This can be done with the helper script
:command:`purge_s4_computer.py`. It must be run on the |UCSPRIMARYDN| or a
|UCSBACKUPDN| system. The query *Really remove Primary Directory Node
from Samba/AD?* must be answered with ``Yes`` and the question *Really
remove Primary Directory Node from UDM as well?* must be answered with ``No``.

For example:

.. code-block:: console

   $ /usr/share/univention-samba4/scripts/purge_s4_computer.py --computername=primary
   Really remove primary from Samba 4? [y/N]: Yes
   If you are really sure type YES and hit enter: YES
   Ok, continuing as requested.

   [...]
   Removing CN=PRIMARY,CN=Computers,$ldap_BASE from SAM database.
   Really remove primary from UDM as well? [y/N]: No
   Ok, stopping as requested.

The Univention S4 connector must be run on the |UCSPRIMARYDN| or a |UCSBACKUPDN|
in the domain. After Samba/AD was uninstalled, the |UCSS4C| join script
:file:`97univention-s4-connector` should be re-executed on the |UCSPRIMARYDN| or
any |UCSBACKUPDN|. This can be done via the |UCSUMC| module :ref:`Domain join
<uv-manual:linux-domain-join-umc>`:

.. _s4connector-rejoin:

.. figure:: /images/s4connector-re-execute.png
   :alt: Re-execute S4 connector join script

   Re-execute S4 connector join script

The FSMO (Flexible Single Master Operations) roles should be checked. In case
the roles were provided by the removed DC, they must be transferred, for
example:

.. code-block:: console

   root@backup:~# samba-tool fsmo show
   InfrastructureMasterRole owner: CN=NTDS Settings,CN=PRIMARY,CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,DC=dom
   RidAllocationMasterRole owner: CN=NTDS Settings,CN=PRIMARY,CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,DC=dom
   PdcEmulationMasterRole owner: CN=NTDS Settings,CN=PRIMARY,CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,DC=dom
   DomainNamingMasterRole owner: CN=NTDS Settings,CN=PRIMARY,CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,DC=dom
   SchemaMasterRole owner: CN=NTDS Settings,CN=PRIMARY,CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,DC=dom

   root@backup:~# samba-tool fsmo seize --role=all --force
   Will not attempt transfer, seizing...
   FSMO transfer of 'rid' role successful
   Will not attempt transfer, seizing...
   FSMO transfer of 'pdc' role successful
   Will not attempt transfer, seizing...
   FSMO transfer of 'naming' role successful
   Will not attempt transfer, seizing...
   FSMO transfer of 'infrastructure' role successful
   Will not attempt transfer, seizing...
   FSMO transfer of 'schema' role successful
   root@backup:~#

.. _ad:

*************************************************
Advanced Active Directory connector documentation
*************************************************

.. _ad-multiple:

Synchronization of several Active Directory domains with one UCS directory service
==================================================================================

It is possible to synchronize several separate Active Directory domains with one
UCS directory service (e.g. to synchronize with an AD forest). One OU
(organizational unit) can be defined in LDAP for each AD domain, under which the
objects of the respective domains are synchronized. The configuration of further
connector instances is not covered by the UMC module.

Several connector instances are started parallel to each other. Each connector
instance is operated with a self-contained configuration base. The
:command:`prepare-new-instance` script is used to create a new instance, e.g.:

.. code-block:: console

   $ /usr/share/univention-ad-connector/scripts/prepare-new-instance \
     -a create -c connector2

This script creates an additional init script for the second connector instance
:file:`/etc/init.d/univention-ad-connector2`, a configuration directory
:file:`/etc/univention/connector2` with a copy of the mapping settings of the
main connector instance (this can be adapted if necessary) and an array of
internal runtime directories.

The additional connector instances are registered in the |UCSUCRV|
:envvar:`connector/listener/additionalbasenames`.

If SSL is used for the connection encryption, the exported Active Directory
certificate must be converted via :command:`openssl` into the required format,
for example:

.. code-block:: console

   $ openssl x509 -inform der -outform pem -in infile.cer -out ad-connector2.pem

The filename of the converted certificate then needs to be stored in |UCSUCR|:

.. code-block:: console

   $ univention-config-registry set \
     connector2/ad/ldap/certificate=/etc/univention/ad-connector2.pem

If a UCS synchronization is performed towards Active Directory, the replication
of the listener module must be restarted after a further connector instance is
created. To this end, the following command must be run:

.. code-block:: console

   $ univention-directory-listener-ctrl resync ad-connector

The command line tools which belong to the AD Connector such as
:command:`univention-adsearch` support selecting the connector instance with the
parameter ``-c``.

.. _bibliography:

************
Bibliography
************


.. bibliography::

