.. _shares-msdfs:

Support for MSDFS
=================

The Microsoft Distributed File System (MSDFS) is a distributed file system which
makes it possible to access shares spanning several servers and paths as a
virtual directory hierarchy. The load can then be distributed across several
servers.

Setting the *MSDFS Root* option for a share (see :ref:`shares-management`)
indicates that the shared directory is a share which can be used for the MSDFS.
References to other shares are only displayed in such an MSDFS root, elsewhere
they are hidden.

To be able to utilize the functions of a distributed file system, the |UCSUCRV|
:envvar:`samba/enable-msdfs` has to be set to ``yes`` on a file server.
Afterwards Samba has to be restarted.

For creating a reference named :file:`tofb` from server ``sa`` within the share
:file:`fa` to share :file:`fb` on the server ``sb``, the following command has
to be executed in directory :file:`fa`:

.. code-block:: console

   $ ln -s msdfs:sb\\fb tofb

This reference will be displayed on every client capable of MSDFS (e.g.
*Windows 2000* and *Windows XP*) as a regular directory.

.. caution::

   Only restricted user groups should have write access to root
   directories. Otherwise, it would be possible for users to redirect
   references to other shares, and intercept or manipulate files. In
   addition, paths to the shares, as well as the references are to be
   spelled entirely in lower case. If changes are made in the
   references, the concerned clients have to be restarted.

   Further information on this issue can be found in
   :cite:t:`samba3-howto-chapter-20`.
