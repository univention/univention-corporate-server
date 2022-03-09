.. _concept-permission:

Permission concept
==================

The permission concept in Univention Corporate Server (UCS) specifies who can
read and write domain data. Permissions apply to objects in the domain database
like users and systems alike. Policies assign custom permissions to objects. UCS
applies default permissions for systems and pre-defined users and groups.

System roles
------------

UCS system roles imply certain permissions on domain data. Only the Primary
Directory Node can write data to the domain database. All other system roles
have read-only access. Nevertheless, other systems or users have write
permissions for certain operations affecting themselves and they run them on the
Primary Directory Node. For example, when a new UCS system joins the domain or
an administrator installs an app write operations run on the Primary Directory
Node.

Administrator and root
----------------------

Some user accounts also have implicit permissions on domain data and systems. A
UCS system knows two administrative user accounts: *Administrator* and *root*.

Administrator
   The user account *Administrator* is the first domain user and has all domain
   permissions. The *Administrator* user account has permission to join new systems to the
   domain and can work with all modules in the UCS management system. The
   account can only be defined once in the domain and must never be renamed.

   The *Administrator* account is only defined once per domain during the
   installation of the Primary Directory Node. The account password is set
   during installation.

   Think of *Administrator* as the primary administrative account for the UCS
   **domain**.

root
   The user account *root* is the superuser on the local UCS system and has the
   user ID of ``0``. It has all permissions and is equivalent to the *root*
   account known from other GNU/Linux systems.

   The *root* account is defined and the password is set during installation of
   every UCS system. The account is only for the local UCS system. On other UCS
   systems administrators should—of course—define different passwords for each
   *root* account.

   Think of *root* as the primary administrative account for the **local** UCS
   system.

   The *root* account has no permissions and is no valid account in the domain
   context. The account *root* must not be created as domain account.

Domain users and admins
-----------------------

To simplify the assignment of certain user permissions, UCS has two default user
groups in the domain that differ fundamentally: *Domain Users* and *Domain
Admins*.

Domain Users
   UCS assigns every user to the user group *Domain Users* per default. The
   group identifies the user account as belonging to a person. The user account
   only has a minimal set of permissions in the domain.

   For example, user accounts in the group can read the domain database, but
   cannot view password hashes. Additional apps in the domain like UCS@school
   and Fetchmail can alter read and write permissions for users and systems.
   User accounts in the *Domain Users* group also cannot log in to UCS systems
   for a remote shell by default. The UCS management system yields no modules
   for them either.

Domain Admins
   UCS creates one user account called *Administrator* during the installation
   of the first UCS system (Primary Directory Node) in a domain. It is the first
   user account and has all permissions for the domain. The *Administrator*
   user account is member of the *Domain Admins* group.

   Users in *Domain Admins* group have all domain permissions just like the
   *Administrator* account. To join a UCS system to the domain, administrators
   need a user account in the group *Domain Admins*.

Machine account
---------------

All systems part of the domain are actors in a domain like users. Each
system has its own account in the domain database. The account is called
*machine account*. Depending on the type of system they have different
permission sets.

UCS systems can read data from the domain database with their machine account.
Every machine account has assigned the following default permissions in the UCS
domain:

.. TODO Add reference to LDAP service and a hint about the LDAP ACLs in the
   referred section. Statements about LDAP and ACLs don't fit in this place.

   The distinct permission for the machine account are defined in LDAP ACLs. See
   /etc/ldap/slapd.conf, the ACL blocks beginning with ``access to ...``

* The UCS system can read all object information and password hashes for
  accounts from the domain database. Apps like UCS@school and Fetchmail limit
  the read permissions.

* The UCS system can write only information to the domain database that is
  associated with its account, for example the version of the installed UCS
  or other apps.

Policies
--------

In addition to the permissions defined for system roles and pre-defined groups,
UCS offers policies for more fine-grained control on administrative settings.

Policies are administrative settings to help administrators with infrastructure
management that can be assigned to objects in the domain database. Policies use
the inheritance principle as it is known from object oriented software
programming. Inheritance allows to set policies to one object in the structured
domain database. The policy then applies to all objects that are organized in
the structure below.
