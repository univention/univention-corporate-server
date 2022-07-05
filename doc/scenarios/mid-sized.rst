.. _engineering:
.. _engineering-start:

*******************************************
Medium-sized mechanical engineering company
*******************************************

Ganupa Technologies is one of the leading manufacturers of rolled steel mills.
At the company headquarters in Germany, 260 people are employed in *Production*,
*Administration*, *Design* and *Sales*. In addition, there are also local offices in
the USA, Argentina and India, each with 5-10 employees.

Linux is predominantly used on the desktops. The employees from *Design* and
*Development* are dependent on Linux software and require a freely configurable
desktop.

The employees from *Administration* and *Sales* will only be offered an office
suite, an email client and a web browser.

An accounting software required by some users is only available for Microsoft
Windows. Part of the design process is performed with a CAD software, which is
only available for Oracle Solaris.

The administration of the computers needs to be as central as possible. Whilst
there are two IT technicians in the headquarters, there are no technical
personnel at the other three branch offices.

To avoid non-productive times caused by malfunctions, the majority of the
offered services must be provided redundantly.

A proxy server will buffer the network traffic in a cache and provide virus
protection.

A groupware solution is required for the coordination of the globally
distributed work procedures.

All user data is centrally saved on an Storage Area Network device (SAN).

.. _engineering-impl:

Implementation
==============

.. _engineering-overview:

.. figure:: /images/mittelstand.*
   :alt: System overview of Ganupa Technologies headquarters (virtualization is not considered)

   System overview of Ganupa Technologies headquarters (virtualization is not considered)

.. _engineering-org-scheme:

.. figure:: /images/mittelstand-ueberblick.*
   :alt: Global organization scheme of Ganupa Technologies

   Global organization scheme of Ganupa Technologies

.. _engineering-dc:

Directory Nodes / LDAP directory
================================

The company implements an infrastructure composed of a UCS |UCSPRIMARYDN|, a UCS
|UCSBACKUPDN|, several UCS |UCSREPLICADN|\ s and desktop systems consisting of
desktop computers and notebooks. Microsoft Windows and Ubuntu Linux are used on
those systems.

The |UCSPRIMARYDN| is the centerpiece of the UCS domain. The central, writable
copy of the LDAP directory service is maintained on this system.

The |UCSBACKUPDN| largely represents a copy of the |UCSPRIMARYDN|. In this way,
the important services are available doubled on the network, the availability of
the services is thus further increased and the load is distributed between the
UCS Directory Nodes.

If the |UCSPRIMARYDN| fails as a result of a hardware defect, the |UCSBACKUPDN|
can be converted to the |UCSPRIMARYDN| in a very short time.

The |UCSPRIMARYDN| and |UCSBACKUPDN| are both installed at the company
headquarters. The two UCS systems operate an LDAP server and provide login
services for the domains. A DNS and DHCP server maintained with data from the
LDAP directory runs on both systems and provides central IP management. A print
server is set up on the |UCSBACKUPDN|.

.. _engineering-print:

Print services
==============

Print jobs are forwarded to the requested printer through a print server. The print
servers are realized with CUPS, which manages the different printers in a
central spooling.

In some larger offices several printers are grouped together into a printer
group; the users simply print on this group, whereby the print jobs are equally
distributed and the next free printer is used. This saves the users from having
to check whether a particular printer is already in use.

.. _engineering-db:

Integration of Oracle Solaris systems
=====================================

A specialist application for CAD design is only available for Oracle Solaris.
The name services on the Solaris system have been adapted to query the UCS LDAP
for authentication. Users can sign in to the Solaris system with their
domain user identification and password. This negates the need for the
additional maintenance of local Solaris user accounts.

The Solaris system is assigned its IP address from the UCS DHCP servers through
DHCP. The files are saved on the UCS file servers through a NFS share.

.. _engineering-storage:

Data management
===============

All user data is stored on a central Storage Area Network (SAN) system. The
different shares are registered and administrated in the |UCSUMC|. The Linux and
Solaris clients connect to individual shares through the network file system
(NFS), the Windows clients through the CIFS protocol.

.. _engineering-groupware:

Groupware
=========

Ganupa Technologies uses the groupware solution :program:`Open-Xchange App
Suite` for arranging meetings and organizing contacts and tasks.

The groupware server is operated as a |UCSREPLICADN| system on the Amazon EC2
cloud. This allows flexible scaling of the groupware system to growing
performance and storage requirements. The installation can be performed with a
few clicks using the App Center.

The administration of the groupware-related attributes integrates seamlessly in
the |UCSUMC|. The employees connect to the groupware through the OX App Suite
web client and Mozilla Thunderbird.

Mobile devices like smartphones and tablets are integrated through the Microsoft
ActiveSync protocol.

Virus detection including signature updates and spam filters are integrated at
no additional cost.

.. _engineering-outlook:

Outlook
=======

At a later point in time, the plan is to monitor the internet traffic centrally
through a web proxy. For this purpose, UCS provides the app :program:`Proxy server/ web cache
(Squid)`.

Alternatively, it is also possible to procure a specialized appliance, which can
authenticate the users against the UCS LDAP server.

.. _engineering-ref:

References
==========

* :ref:`UCS Manual <uv-manual:introduction>`

* `OX App Suite
  <https://www.univention.com/products/univention-app-center/app-catalog/oxseforucs/>`_

* `Proxy server/ web cache (Squid)
  <https://www.univention.com/products/univention-app-center/app-catalog/squid/>`_
