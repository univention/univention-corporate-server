.. _classification:

******************************
Classification in the IT world
******************************

To comprehend the architecture of Univention Corporate Server (UCS) it is
important to understand the origin and where it is located in the world of
information technology (IT).

Origin
======

UCS is a Linux distribution derived from `Debian GNU/Linux <w-debian_>`_. Among
others, it benefits from the strong package manager, the high quality
maintenance and the long-term stability as operating system for servers. Over
the years, Debian has been and is a solid basis for UCS.

UCS is part of the open source family and has strong relations to important
projects like for example `Samba <w-samba_>`_ and `OpenLDAP <w-openldap_>`_.

History
-------

Univention started UCS in 2002 as a collection of scripts that turn a Debian
system into a Linux server that offers Windows domain functionality. The goal
was to offer companies and organizations a standardized Linux server as
alternative to Microsoft Windows Server that implements Microsoft's domain
concept. Over the time it developed to an enterprise Linux distribution with
maintenance cycles that better suited organizations.

Packages
--------

Packages on UCS use the deb file format, which is a standard Unix *ar archive*
including two *tar archives*. One holds control information and the other the
data for installation. For more information on the deb file format, see `dev (file
format) at Wikipedia <w-deb-file-format_>`_ and `Basics of the Debian package
management system in the Debian FAQ <debian-faq-pkg-basics_>`_.

UCS like Debian uses a package manager, which is a collection of software tools,
to automate the process of installation, upgrade, configuration and removal of
computer programs. In UCS the package manager is the advanced package tool
(APT). For more information about APT, see the `Debian package management
chapter in the Debian reference <debian-ref-package-mngmt_>`_.

Univention distributes most packages from Debian GNU/Linux for the *amd64*
architecture without changes for UCS. This includes the GNU/Linux kernel offered
by Debian and about xx% of the packages.

.. TODO Ask SME: For some rough statistics
   TODO Ask SME: How many packages do we copy from Debian? How many of them are changed by Univention? Do we copy all packages?
   TODO Ask SME: How many packages are added by Univention?

In the following circumstances, Univention builds and maintains derived
packages:

* A later software version of a package is needed for UCS than Debian offers.
* Bug fixes or backports of a specific software are needed for a package.

Additionally, Univention develops software responsible for UCS functionality
that is distributed as Debian package.

Identity management
===================

The most important functional pillar of UCS is identity management.

Simplified, an IT environment consists of services and users. Services offer
functionality. Users use functionality. Services can also behave as users
when they use the functionality of another service. Actors identify themselves
against services to proof that they are eligible to use the functionality.

The identification is done with *user accounts* to represent users. User
accounts typically have properties like for example username, password and email
address. User accounts that digitally represent a person additionally have for
example first name and last name.

Imagine a small IT environment with 20 persons and five systems. Without a
central identity management, an administrator would have to maintain 20 user
accounts on each of the five systems. The management effort sums up to 100
items. The number of items to manage is a linear function. The function's slope
increases with the number of systems that need to know user accounts.

With a central identity management, one service holds the information about the
user accounts. All other services have access to that information. An
administrator only has to maintain the user accounts on that system. The
maintenance effort for the user accounts does not anymore multiply with the
number of systems that need to know the user accounts. The slope of this linear
function is less steep.

Central identity management reduces the maintenance effort of user accounts for
administrators.

UCS is a product for central identity management for user accounts, their
permissions and the collection of user accounts in groups.

Infrastructure management
=========================

The second important functional pillar of UCS is IT infrastructure management.

IT infrastructure is a set of IT components like computer and networking
hardware, various software and network components. It is the foundation of an
organization's technology system and drives the organization's success.

UCS provides important infrastructure services to create an IT network
infrastructure and connect IT components. UCS assigns addresses with DHCP and
resolves hostnames with DNS, and much more. Administrators manage various IT
components in their IT environment, like different kind of hosts, clients and
printers.

For more information about the different infrastructure services in UCS, see
:ref:`services`.

Connection to the world around
==============================

As operating system offering many services, UCS interacts with its surrounding
peers. Actors access the functionality of UCS through the following ways:

Web
   Persons like administrators and also end users use HTTPS to access the web
   based UCS management system. In many cases other web-based services provided
   by other software products delivered through apps are available through
   HTTPS.

Console
   Persons with more technical background and the appropriate permissions can
   access UCS through a console, either on a local terminal or through a remote
   SSH session.

Service protocols
   As soon as users use any of the services that UCS offers, they access UCS
   through one of those protocols. For example, a user's client requests
   and IP address through DHCP and later asks for the IP address of the print
   server.

As a central system offering identity and infrastructure management UCS has to
use numerous ways of connections.
