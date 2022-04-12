.. _windows-services-for-windows:

********************
Services for Windows
********************

UCS can offer Active Directory (AD) services, be a member of an Active Directory
domain or synchronize objects between Active Directory domains and a UCS domain.

For the purposes of Windows systems, UCS can assume the tasks of Windows server
systems:

* Domain controller function / authentication services

* File services

* Print services

In UCS all these services are provided by Samba.

UCS supports the mostly automatic migration of an existing Active Directory
domain to UCS. All users, groups, computer objects and group policies are
migrated without the need to rejoin the Windows clients. This is documented in
:ref:`windows-adtakeover`.

Microsoft Active Directory domain controllers cannot join the Samba domain. This
functionality is planned at a later point in time.

Samba can not join an Active Directory Forest yet at this point.

Incoming trust relationships with other Active Directory domains are
configurable. In this setup the external Active Directory domain trusts
authentication decisions of the UCS domain (Windows trusts UCS) so that UCS
users can log in to systems and Active Directory backed services in the Windows
domain (see :ref:`windows-trust`). Outgoing trusts with Active Directory domain
(UCS trusts Windows) are not supported currently.

.. toctree::
   :caption: Chapter contents

   samba-domain
   ad-connection
   ad-takeover
   trust
