.. _shares-general:

*********************
File share management
*********************

UCS supports the central management of directory shares. A share registered via
the UMC module :guilabel:`Shares` is created on an arbitrary UCS server system
as part of the UCS domain replication.

Provision for accessing clients can occur via CIFS (supported by Windows/Linux
clients) and/or NFS (primarily supported by Linux/Unix).  The NFS shares managed
in the UMC module can be mounted by clients both via NFSv3 and via NFSv4.

If a file share is deleted on a server, the shared files in the directory are
preserved.

To be able to use access control lists on a share, the underlying Linux file
system must support POSIX ACLs. In UCS the file systems ``ext4`` and ``XFS``
support POSIX ACLs. The Samba configuration also allows storing DOS file
attributes in extended attributes of the Unix file system. To use extended
attributes, the partition must be mounted using the mount option ``user_xattr``.

.. toctree::
   :hidden:

   access-rights
   umc
   msdfs
   quota
