.. _lawyer:
.. _lawyer-start:

***************
Lawyer's office
***************

Hemmerlein & Sons lawyer's office has a total of ten employees. The employees
work predominantly with office applications and a legal workflow management
system, which is only available for Microsoft Windows. Windows is employed as
the client operating system. All the data is to be stored centrally on a server
and backed up. As there is only limited technical expertise available and it is
not viable to finance an in-house administrator team, particular value is placed
on simple administration. The administrative duties described below can be
configured completely through simple-to-use, web-based interfaces after a successful
initial installation.

The company has a total of three laser printers (two identical black/white
models and one color laser printer), which are all installed in a central
office. Large documents with high volumes are printed often.

.. _lawyer-services:

Systems and services
====================

UCS offers the required services and applications out of the box as a
complete solution. A single UCS system is used, which provides the logon and
file services for the Windows clients, administrates the printers and automates
the data backup.

.. _law-office:

.. figure:: /images/kanzlei.*
   :alt: System overview of the lawyer's office Hemmerlein and Sons

   System overview of the lawyer's office Hemmerlein and Sons

.. _lawyer-users:

Management of user accounts
===========================

User accounts for the ten employees are created in the |UCSUMC| web interface.
Each employee can set the password with the :program:`Self Service` app from the
App Center. Like all user data the password is saved to a LDAP directory server
and requested when logging on to the Windows client.

.. _create-user:

.. figure:: /images/umc-benutzeranlegen.*
   :alt: Creating a user in Univention Directory Manager

   Creating a user in Univention Directory Manager

.. _lawyer-windows:

Managing the Windows computers
==============================

Samba 4 is used on the UCS system for the integration of Microsoft Windows
clients. Samba 4 offers domain, directory and authentication services which are
compatible with Microsoft Active Directory. These also allow the use of the
tools provided by Microsoft for the management of group policies (GPOs).

Microsoft Windows clients can join the Active Directory-compatible domain
provided by UCS and can be centrally configured through group policies. From the
client point of view, the domain join procedure is identical to joining a
Microsoft Windows-based domain.

.. _lawyer-storage:

Storage management
==================

Samba provides every user with a home directory on the UCS system as a file
share through the CIFS protocol. The users thus always receive the same data
irrespective of the computer they are logged in to. In addition, the central file
storage allows central backups.

Moreover, there is a central share with legal literature, which is mounted on
every client.

Similar to users, shares can also be created and managed web-based in the
|UCSUMC|.

.. _lawyer-sso:

Single sign-on with a specialist legal application
==================================================

The chambers connect to a web-based legal service. This service has its own user
administration system. To avoid having to take care of the user identities and
password twice, the UCS SAML Identity Provider is used. SAML (Security Assertion
Markup Language) is an XML-based standard for exchanging authentication
information, which allows single sign-on across domain boundaries among other
things. The legal service is registered with a cryptographic certificate and
then trusted by the UCS Identity Provider. The users then only need to
authenticate themselves in UCS and can use the legal service without renewed
authentication. The SAML Identity Provider can be installed through the Univention
App Center.

.. _lawyer-print:

Printer services
================

The UCS system provides print services through the CUPS software. Both
network-capable printers and printers connected locally to a computer can be
centrally administrated. The three printers can be configured conveniently
through
the |UCSUMC| and are directly available to the users on their Microsoft Windows
clients.

The two black and white laser printers are grouped together in a printer group:
this means that, in addition to the targeted selection of a printer, users also
have the opportunity of printing on a pseudo-printer. This is where the print
jobs are distributed in turn between the two printers in the printer group. If
one printers is busy, the free printer is selected instead, which cuts down
waiting times.

.. _lawyer-groupware:

Groupware
=========

On the UCS system the groupware solution :program:`Kopano` is installed as app
from the App Center. Kopano accesses the user data of the UCS directory service.
The administration integrates seamlessly in the |UCSUMC|. The employees use the
web-based :program:`Kopano WebApp` for calendaring, also available in the App
Center.

Virus detection including signature updates and spam filters are integrated at
no additional cost.

.. _lawyer-proxy:

Web proxy and web cache
=======================

A web proxy server and web cache based on Squid is available with the app
:program:`Proxy server` in UCS. Response times for regular calling the same web
pages is reduced. Likewise, the data transfer volume through internet
connections can be reduced. Furthermore, the view of internet content can be
controlled and managed. For example, it can be defined, which users or user
groups view which websites.

.. _lawyer-backup:

Backup
======

All files, both the users' files in the home directory and the legal literature
files in the central share, are stored on the UCS system and can thus be
centrally saved on a tape drive. The App Center in UCS offers several solutions
like for example :program:`Bareos Backup Server` and :program:`SEP sesam Backup
Server` that can be used flexibly for different backup and archiving strategies.

.. _lawyer-outlook:

Outlook
=======

With regard to a planned merger of another office in Munich, it will be simple
to install a further UCS system in this branch. All LDAP data is then
automatically transferred to the site server allowing the employees to logon at
on-site meetings in Munich with their standard user credentials.

The existing Active Directory installation at the Munich office can be migrated
to the UCS domain fully automated using :program:`Univention AD Takeover`.

.. _lawyer-ref:

References
==========

* :ref:`UCS Manual <uv-manual:introduction>`

* :ref:`uv-manual:windows-ad-takeover`

* `Bareos Backup Server
  <https://www.univention.com/products/univention-app-center/app-catalog/bareos/>`_

* `Kopano Core
  <https://www.univention.com/products/univention-app-center/app-catalog/kopano-core/>`_

* `Kopano WebApp
  <https://www.univention.com/products/univention-app-center/app-catalog/kopano-webapp/>`_

* `Proxyserver / Webcache (Squid)
  <https://www.univention.com/products/univention-app-center/app-catalog/squid/>`_

* `Self Service <https://www.univention.com/products/univention-app-center/app-catalog/self-service/>`_

* `SEP sesam Backup Server
  <https://www.univention.com/products/univention-app-center/app-catalog/sep-sesam/>`_



.. spelling::

   Munich
