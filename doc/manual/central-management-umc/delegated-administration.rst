.. _delegated-administration:

Delegated administration for UMC modules
========================================

By default only the members of the ``Domain Admins`` group can access all UMC
modules. Policies can be used to configure the access to UMC modules for groups
or individual users. For example, this can be used to assign a helpdesk team the
authority to manage printers without giving them complete access to the
administration of the domain.

UMC modules are assigned via a *UMC* policy which can be assigned to user and
group objects. The evaluation is performed additively, i.e., general access
rights can be assigned via ACLs assigned to groups and these rights can be
extended via ACLs bound to user (see :ref:`central-policies`).

In addition to the assignment of UMC policies, LDAP access rights need to be
taken into account, as well, for modules that manage data in the LDAP directory.
All LDAP modifications are applied to the whole UCS domain. Therefore by default
only members of the ``Domain Admins`` group and some internally used accounts
have full access to the UCS LDAP. If a module is granted via a UMC policy, the
LDAP access must also be allowed for the user/group in the LDAP ACLs. Further
information on LDAP ACLs can be found in :ref:`domain-ldap-acls`.

.. list-table:: Policy 'UMC'
   :header-rows: 1

   * - Attribute
     - Description

   * - List of allowed UCS operation sets
     - All the UMC modules defined here are displayed to the user or group to
       which this ACL is applied. The names of the domain modules begin with
       'UDM'.

.. caution::

   For access to UMC modules, only policies are considered that are assigned to
   groups or directly to user and computer accounts. Nested group memberships
   (i.e., groups in groups) are not evaluated.
