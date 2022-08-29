.. _central-portal:

UCS portal page
===============

Portal pages offer a central view of all available services in a UCS domain.
Requirements strongly differ from small to large environments in organizations,
public authorities, or even schools. Therefore, UCS implemented a very flexible
and individually customizable concept for portal pages.

As illustrated in :numref:`portal-schema`, portal entries (i.e., links
to applications/Apps/services; UDM object type ``portals/entry``) can be
assigned to none, one or multiple portal categories. A portal category
(UDM object type ``portals/category``) can be assigned to none, one or
multiple portals. A portal itself (UDM object type ``portals/portal``)
renders all portal categories which are assigned to it.

The portal *domain*, shipped with every installation, is configured on each
server by default. In addition to all installed applications of the domain,
links to |UCSUMC| as well as the server overview are shown on this portal page.

To change the displayed portal, the |UCSUCRV| :envvar:`portal/default-dn` must
be adjusted. After a change, the :program:`univention-portal-server` service
must be restarted.

Custom portals and portal entries can be defined and managed either via the UMC
module :guilabel:`Portal` or directly on the portal site.

After logging in to the portal on the |UCSPRIMARYDN| or |UCSBACKUPDN|, members
of the ``Domain Admins`` group can edit the portal after clicking on the
corresponding entry in the user menu. They now can create new entries on the
portal, modify existing entries, modify the order or the design.

Advanced settings, such as adding new portals or setting which group members can
see which portal entries can be made using the UMC portal settings module.

By default, all portal entries are displayed for everyone. In the UMC module
:guilabel:`Portal` in the category *Login*, it can be configured whether
anonymous visitors have to sign in before they can see entries. It is also
possible to limit certain entries for certain groups. This requires the LDAP
attribute ``memberOf``. Nested group memberships (i.e., groups in groups) are
evaluated.

Further design adjustments can be made in the file
:file:`/usr/share/univention-portal/css/custom.css`. This file will not be
overwritten during an update.

.. _portal-schema:

.. figure:: /images/portal-schema.*
   :alt: Schema of the portal concept in UCS

   Schema of the portal concept in UCS: Portals can be independently defined and
   assigned to UCS systems as start site; a link entry can be displayed on
   multiple portals.

.. _central-management-umc-assignment-of-portal-settings-module:

Assign rights for portal settings
---------------------------------

The following describes how to make the UMC module :guilabel:`Portal` accessible
to selected groups or users. This example assumes that a group
``Portal Admins`` has been created and members of this group are
supposed to be given access to the portal settings.

On a |UCSPRIMARYDN| an ACL file has to be created first, for example
:file:`/opt/62my-portal-acl.acl`. This file has to have the following content
to allow the necessary ACL changes:

.. code-block::

   access to dn="cn=portals,cn=univention,@%@ldap/base@%@" attrs=children
     by group/univentionGroup/uniqueMember="cn=Portal Admins,cn=groups,@%@ldap/base@%@" write
     by * +0 break

   access to dn.children="cn=portals,cn=univention,@%@ldap/base@%@" attrs=entry,@univentionObject,@univentionNewPortalEntry,
   @univentionNewPortal,@univentionNewPortalCategory,children
     by group/univentionGroup/uniqueMember="cn=Portal Admins,cn=groups,@%@ldap/base@%@" write
     by * +0 break


Then execute the following command to create an LDAP object for the LDAP ACLs:

.. code-block:: console

   $ udm settings/ldapacl create \
     --position "cn=ldapacl,cn=univention,$(ucr get ldap/base)" \
     --set name=62my-portal-acl \
     --set filename=62my-portal-acl \
     --set data="$(bzip2 -c /opt/62my-portal-acl.acl | base64)" \
     --set package="62my-portal-acl" \
     --set packageversion=1


If the ACL is to be deleted again, the following command can be used:

.. code-block::

   udm settings/ldapacl remove \
     --dn "cn=62my-portal-acl,cn=ldapacl,cn=univention,$(ucr get ldap/base)"

An appropriate UMC policy can now be created via UMC. The following
*UMC operations* must be allowed within the policy:

* *udm-new-portal*
* *udm-syntax*
* *udm-validate*
* *udm-license*

How to create a policy is described in
:ref:`central-management-umc-create-policy`. Now the newly created policy only
needs to be assigned to the wanted object, in this case the group ``Portal
Admins``. This can also be done directly within the UMC. For this example,
navigate to the group module and edit the wanted group there. In the group
settings, existing policies for the group object can be selected under
:guilabel:`Policies`. More detailed information about policy assignment is
described under :ref:`central-policies-assign`.
