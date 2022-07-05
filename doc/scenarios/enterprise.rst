.. _insurance:
.. _insurance-start:

************************************************************
Heterogeneous enterprise environment in an insurance company
************************************************************

*Hanseatische Marineversicherung* (HMV) is an insurance company with 1800
employees specialized in the logistics sector. HMV is a subsidiary of the Vigil
Insurances parent company.

The parent company operates an independent directory service based on Microsoft
Active Directory, but the user data of the individual subsidiaries is managed
internally.

The employees work at a total of 36 locations across the world with the largest
being the company headquarter in Bremen with approximately 250 persons. Many of
the users work on the move with laptops as salespersons or estimators.

Microsoft Windows is used on all the desktops. Software distribution and the
installation of security updates are centralized.

Citrix XenApp needs to be employed in the headquarters because of a
superordinate group policy: users connect to the terminal services with thin
clients.

The groupware Microsoft Exchange is provided centrally by the parent company.

All users, computers and services need to be centrally administrable. Critical
system status is reported promptly per email and SMS.

All server systems in the headquarters need to be virtualized. The resulting
considerable significance of virtualization requires the implementation of an
open source solution.

Data backup is performed centrally in Bremen.

Different international compliance requirements from the insurance sector must
be satisfied.

A special application for insurance business runs on a Power7 system with IBM
AIX. The users on this system don't need to be maintained twice.

.. _insurance-impl:

Implementation
==============

The company implements an infrastructure composed of a UCS |UCSPRIMARYDN|, a UCS
|UCSBACKUPDN|, several UCS |UCSREPLICADN|\ s and 150 thin clients.

The |UCSPRIMARYDN| is the centerpiece of the UCS domain. The central, writable
LDAP directory is provided on this system.

.. _insurance-overview:

.. figure:: /images/versicherung.*
   :alt: General overview (excluded: storage, DNS, DHCP, print services, virtualization, backup)

   General overview (excluded: storage, DNS, DHCP, print services, virtualization, backup)

The |UCSBACKUPDN| also largely represents a copy of the |UCSPRIMARYDN|. In this
way, the important services are available doubled on the network, the
availability of the services is thus further increased and the load is
distributed between the Directory Nodes.

If the |UCSPRIMARYDN| fails as a result of a hardware defect, the |UCSBACKUPDN|
can be converted to the |UCSPRIMARYDN| in a very short time.

The |UCSPRIMARYDN| and |UCSBACKUPDN| are both installed at the company
headquarters. The locations also contain additional |UCSREPLICADN| systems,
which provide Windows domain services, print services and software distribution.

.. _insurance-location:

.. figure:: /images/versicherung-standort.*
   :alt: Structure of a location

   Structure of a location

.. _insurance-software:

Software distribution of UCS systems
====================================

Installation profiles have been created for the UCS Directory Nodes. These
profiles can be used to roll out additional systems with the Univention Net Installer
using PXE or, as required, to restore systems after hardware failure. The
installation concludes without further user interaction.

A central package installation source - the repository - is established on a
server in the headquarters for the installation of release updates and the
subsequent installation of software packages. All software packages available
for installation and updates are provided there.

Policies in the |UCSUMC| can be used to control the software distribution
centrally. The updates can be installed or software packages can be subsequently
installed at a freely selectable time or when shutting down or starting up the
system.

All systems record the installed packages in a central SQL database
automatically so that an overview of the software inventory is always available.
Security updates for UCS are promptly provided to download and can also be
installed automatically.

.. _insurance-windows:

Connecting Windows clients and Windows software deployment
==========================================================

Samba/AD is used in the HMV for the integration of Microsoft Windows clients.
Samba/AD offers domain, directory and authentication services which are
compatible with Microsoft Active Directory. These also allow the use of the
tools provided by Microsoft for the management of group policies (GPOs).

Windows clients can join the Active Directory-compatible domains provided by UCS
directly and can be centrally configured through group policies. From the client
point of view, the domain join procedure is identical to joining a Windows-based
domain.

The open source software distribution :program:`opsi` runs on the Windows
clients. It allows an extensively automated distribution of security updates and
Windows updates as well as the rollout of software packages to the Windows
clients.

opsi is also used to rollout additional Windows systems. These are automatically
installed through PXE.

.. _insurance-ad:

Active Directory synchronization
================================

The :program:`Univention Active Directory Connector` makes it possible to synchronize
directory service objects between a Microsoft Windows 2012/2016/2019 server with
Microsoft Active Directory (AD) and an open source LDAP directory service in
|UCSUCS|.

The synchronization settings can be specified individually. The administrator
thus has the possibility of controlling the synchronization precisely and only
synchronizing selected objects and attributes.

The UCS directory service synchronizes with the Microsoft Active Directory of
the parent company. The replication encompasses all the containers,
organizational units, users and groups.

The computer accounts are not synchronized, as Windows computers can only be
joined in one domain. All Windows clients are joined in the UCS Samba/AD domain.

.. _insurance-groupware:

Groupware
=========

The groupware is provided in the form of Exchange Server 2016 by the parent
company Vigil Insurances, allowing the users to connect to it using Outlook and
Outlook on the web.

The integration of the UCS directory service and the Active Directory of the
parent company allows authentication with the same username / password.

Users can connect to the services of both environments in a transparent way, as
the same user settings apply in both domains. For example, a user can sign in
both the UCS directory service on their laptop and the Citrix Server in the
Microsoft Active Directory with the same username and password.

.. _insurance-compliance:

Compliance requirements
=======================

HMV must satisfy a range of insurance industry compliance requirements.

* All LDAP write accesses must be verifiable. This is done by means of the
  Univention Directory Logger. This transcribes each LDAP change in a secure
  transaction log file, which is protocolized audit-compliantly with checksums.

* The user data must be available immediately for external audit purposes. To do
  so, Univention Directory Reports can be used to create a PDF document or a CSV
  file of all or some users and groups from the |UCSUMC|.

* Quality standards must be established for passwords. In UCS, for example, one
  can set a minimum number of lowercase and uppercase characters, symbols or
  figures for passwords. In addition, passwords can be compared against a list
  of unsafe passwords, for example ``secret``.

.. _insurance-monitoring:

System monitoring with Nagios NRPE
==================================

UCS integrates the system monitoring software Nagios through NRPE, which allows the
monitoring of complex IT structures from networks, computers and services. This
includes a comprehensive range of monitoring modules, which can also be expanded
if necessary.

.. _insurance-aix:

Integration of the AIX system
=============================

The insurance policies are administrated with an application which can only be
operated on highly available Power7 systems using IBM AIX.

In the past, all users working on the system were maintained twice in the local
user database of the AIX system. Now only the ``secldapclntd`` service runs on
the AIX system; it performs all the authentication processes against the UCS
LDAP directory.

.. _insurance-terminal:

Citrix terminal services
========================

In the headquarters 150 users work with terminal services based on Citrix
XenApp. The XenApp terminal server runs on a Windows member server, which joined
the local Samba/AD domain.

.. _insurance-backup:

Backup
======

:program:`SEP sesam backup server` from the App Center is used for file backup,
which can be installed with a few clicks. It offers a distributed backup concept
with different backup agents, which backup both complete systems and data.
Special backup agents are available for the backup of databases. All data is
copied from the standard servers in the headquarters and from there saved on
tape media. The installation can be performed with a few clicks in the App
Center.

.. _insurance-crm:

Integration of SuiteCRM
=======================

:program:`SuiteCRM` is employed as the CRM solution for sales personnel. The
administration of the SuiteCRM users and roles integrates directly in the
|UCSUMC|. The installation can be performed with a few clicks using the
Univention App Center.

The installation is operated as a |UCSREPLICADN| system on the Amazon EC2 cloud.
This ensures high availability and allows flexible scaling to growing
performance and storage requirements.

.. _insurance-ref:

References
==========

* :ref:`UCS Manual <uv-manual:introduction>`

* :ref:`uv-manual:domain-ldap-directory-logger`

* `Extended installation documentation
  <https://docs.software-univention.de/installation-5.0.html>`_

* `opsi
  <https://www.univention.com/products/univention-app-center/app-catalog/opsi/>`_

* `SEP sesam Backup Server
  <https://www.univention.com/products/univention-app-center/app-catalog/sep-sesam/>`_

* `SuiteCRM
  <https://www.univention.com/products/univention-app-center/app-catalog/digitec-suitecrm/>`_

.. spelling::

   checksums
   protocolized
