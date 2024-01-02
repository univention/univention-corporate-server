.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _shares-management:

Management of shares via UMC module
===================================

File shares are managed in the UMC module :guilabel:`Shares`
(see :ref:`central-user-interface`).

When adding/editing/deleting a share, it is entered, modified or removed
in the :file:`/etc/exports` file and/or the Samba
configuration.

.. _shares-umc:

.. figure:: /images/projekt-freigabe.*
   :alt: Creating a share via the UMC module *Shares*

   Creating a share via the UMC module :guilabel:`Shares`

.. _shares-management-general-tab:

Shares UMC module - General tab
-------------------------------

.. _shares-management-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Name
     - The name of the share is to be entered here. The name must be composed
       of letters, numerals, full stops or blank spaces and must begin and end
       with a letter or numeral.

   * - Comment
     - A free selectable description for this share.
       This is also displayed in the file browser in Windows.

   * - Host
     - The server where the share is located. All of the Primary/Backup/\
       |UCSREPLICADN| computers and |UCSMANAGEDNODE|\ s entered in the LDAP
       directory for the domain are available for selection which are entered in
       a DNS forward lookup zone in the LDAP directory.

   * - Directory
     - The absolute path of the directory to be shared, without quotation marks
       (this also applies if the name includes special characters such as
       spaces). If the directory does not exist, it will be created
       automatically on the selected server.

       If the |UCSUCRV| :envvar:`listener/shares/rename` is set to ``yes``, the
       contents of the existing directory are moved when the path is modified.

       No shares can be created in and below :file:`/proc`, :file:`/tmp`,
       :file:`/root`, :file:`/dev` and :file:`/sys` and no files can be moved
       there.

   * - Directory owner of the share's root
     - The user to whom the root directory of the share should belong, see
       :ref:`shares-permissions`.

   * - Directory owner group of the share's root
     - The group to whom the root directory of the share should belong, see
       :ref:`shares-permissions`.

   * - Permissions for the share's root
     - The read, write and access permissions for the root directory of the
       share, see :ref:`shares-permissions`.

.. _shares-management-nfs-tab:

Shares UMC module - NFS tab
---------------------------

Shares UMC module - NFS group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. _shares-management-nfs-tab-table:

.. list-table:: *NFS* group
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - NFS write access
     - Allows NFS write access to this share; otherwise the share can only be
       used in read-only mode.

   * - Subtree checking
     - If only one subdirectory of a file system is exported, the NFS server has
       to check whether an accessed file is located on the exported file system
       and in the exported path, each time access is made. Path information is
       passed on to the client for this check. Activating this function might
       cause problems if a file opened by the client, is renamed.

   * - Modify user ID for root user (root squashing)
     - In the NFS standard procedure, identification of users is achieved via
       user IDs. To prevent a local root user from working with root permissions
       on other shares, root access can be redirected. If this option is
       activated, access operations are executed as user ``nobody``.

       The local group ``staff``, which is by default empty, owns privileges
       which come quite close to ``root`` permissions, yet this group is not
       considered by the redirection mechanism. This fact should be borne in
       mind when adding users to this group.

   * - NFS synchronization
     - The synchronization mode for the share. The ``sync`` setting is used to
       write data directly on the underlying storage device. The opposite
       setting - ``async`` - can improve performance but also involves the risk
       of data loss if the server is shut down incorrectly.

   * - Only allow access for these hosts, IP addresses or networks
     - By default, all hosts are permitted access to a share. In this selection
       list, host names and IP addresses can be included, to which the access to
       the share is to be restricted. For example, access to a share containing
       mail data could be restricted to the mail server of the domain.

.. _shares-management-nfs-custom-settings-group:

Shares UMC module - NFS custom settings group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _shares-management-nfs-custom-settings-tab-table:

.. list-table:: *NFS custom settings* group
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Custom NFS share settings
     - Apart from the properties in the *NFS* group, this setting makes
       it possible to define further arbitrary NFS settings for the share. A
       list of available options can be obtained by the command :command:`man 5
       exports`. Double entries of configuration options are not checked.

.. caution::

   The definition of extended NFS settings is only necessary in special cases.
   The options should be thoroughly checked since they might have
   security-relevant effects.

.. _shares-management-samba-tab:

Shares UMC module - Samba tab
-----------------------------

Shares UMC module - Samba group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _shares-management-samba-group-table:

.. list-table:: *Samba* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Windows name
     - The NetBIOS name of the share. This is the name under which the share is
       displayed on Windows computers in the network environment. When adding a
       directory share, the UMC module adopts the name entered in the *Name*
       field of the *General* tab as the default.

   * - Show share in Windows network environment
     - Specifies whether the share in question is to show up on Windows clients
       within the network environment.

   * - Allow anonymous read-only access with a guest user
     - Permits access to this share without a password. Every access is carried
       out by means of the common guest user ``nobody``.

   * - Export share as MSDFS root
     - This option is documented in :ref:`shares-msdfs`.

   * - Hide unreadable files/directories
     - If this option is activated, all files which are not readable for the user
       due to their file permissions, will be hidden.

.. _shares-management-samba-permissions-group:

Shares UMC module - Samba permissions group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _shares-management-samba-permissions-group-table:

.. list-table:: *Samba permissions* group
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Users with write access may modify permissions
     - If this option is activated, all users with write permission to a file
       are allowed to change permissions, ACL entries, and file ownership
       rights, see :ref:`shares-permissions`.

   * - Force user
     - This username and its permissions and primary group is used for
       performing all the file operations of accessing users. The username is
       only used once the user has established a connection to the Samba share
       by using their real username and password. A common username is useful for
       using data in a shared way, yet improper application might cause security
       problems.

   * - Force group
     - A group which is to be used by all users connecting with this share, as
       their primary group. Thereby, the permissions of this group automatically
       apply as the group permissions of all these users. A group registered
       here has a higher priority than a group which was assigned as the primary
       group of a user via the *Force user* entry field.

       If a ``+`` sign is prefixed to the group name, then the group is assigned
       as a primary group solely to those users which are already members of
       this group. All other users retain their primary groups.

   * - Valid users or groups
     - Names of users or groups which are authorized to access this Samba share.
       To all other users, access is denied. If the field is empty, all users
       may access the share - if necessary after entering a password. This
       option is useful for securing access to a share at file server level
       beyond the file permissions.

       The entries are to be separated by spaces. The special characters ``@``,
       ``+`` and ``&`` can be used in connection with the group name for
       assigning certain permissions to the users of the stated group for
       accessing the Samba share:

       * A name beginning with the character ``@`` will first be interpreted as
         a NIS net-group. Should no NIS net-group of this name be found, the name
         will be considered as a UNIX group.

       * A name beginning with the character ``+`` will be exclusively
         considered as a UNIX group, a name beginning with the character ``&``
         will be exclusively considered as a NIS net-group.

       * A name beginning with the characters ``+&``, will first be interpreted
         as a UNIX group. Should no UNIX group of this name be found, the name
         will be considered as a NIS net-group. The characters ``&+`` as the
         beginning of a name correspond to the character ``@``.

   * - Invalid users or groups
     - The users or groups listed here cannot access the Samba share. The syntax
       is identical to the one for valid users. If a user or group is included
       in the list of valid users and unauthorized users, access is denied.

   * - Restrict read access to these users/groups
     - Only the users and groups listed here have read permission for the
       corresponding share.

   * - Restrict write access to these users/groups
     - Only the users and groups listed here have write permission for the
       corresponding share.

   * - Allowed hosts/networks
     - Names of computers which are authorized to access this Samba share. All
       other computers are denied access. In addition to computer names, it is
       also possible to specify IP or network addresses, e.g.,
       ``192.0.2.0/255.255.255.0``.

   * - Denied hosts/networks
     - The opposite to the authorized computers. If a computer appears in both
       lists, the computer is permitted to access the Samba share.

   * - Inherit ACLs
     - When activating this option, each file created in this share will inherit
       the ACL (Access Control List) of the directory where the file was
       created.

   * - Create files/directories with the owner of the parent directory
     - When activating this option, each newly created file will not be assigned
       of the user who created the file, but to the owner of the superior
       directory instead.

   * - Create files/directories with permissions of the parent directory
     - When activating this option, for each file or directory created in this
       share, the UNIX permissions of the superior directory will automatically
       be adopted.

If a new file is created on a Samba server from a Windows client, the
file permissions will be set in several steps:

1. First, only the DOS permissions are translated into UNIX permissions.

2. Then the permissions are filtered via the *Filemode*. UNIX permissions which
   are marked in *File mode*, are the only ones preserved. Permissions not set
   here, will be removed. Thus, the permissions have to be set as UNIX
   permissions and in *File mode* in order to be preserved.

3. In the next step, the permissions under *Force file mode* are added. As a
   result, the file will have all the permissions set after step 2 or under
   *Force file mode*. This means, permissions marked under *Force file mode* are
   set in any case.

Accordingly, a newly created directory will initially be assigned the same
permissions as that which are set as UNIX permissions and in *Directory mode* at
the same time. Then these permissions are completed by those marked under *Force
directory mode*.

.. _shares-management-samba-permissions-extended-group:

Shares UMC module - Samba extended permissions group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _shares-management-samba-permissions-extended-group-table:

.. list-table:: *Samba extended permissions* group
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - File mode
     - The permissions Samba is to adopt when creating a file, provided they are
       set under Windows.

   * - Directory mode
     - The permissions Samba is to adopt when creating a directory, provided
       they are set under Windows.

   * - Force file mode
     - The permissions Samba is to set in any case when creating a file,
       irrespective of whether they are set under Windows or not.

   * - Force directory mode
     - The permissions Samba is to set in any case when creating a directory,
       irrespective of whether they are set under Windows or not.

.. _shares-management-samba-options-group:

Shares UMC module - Samba options group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _shares-management-samba-options-group-table:

.. list-table:: *Samba options* group
   :header-rows: 1
   :widths: 2 10

   * - Attribute
     - Description

   * - VFS Objects
     - Virtual File System (VFS) modules are used in Samba for performing
       actions before an access to the file system of a share is made, e.g., a
       virus scanner which stores every infected file accessed in the share in
       quarantine or server-side implementation of recycle bin deletion of
       files.

   * - Hidden files
     - Files and directories to be accessed under Windows, yet not to be
       visible. Such files or directories are assigned the DOS attribute
       *hidden*.

       When entering the names of files and directories, upper and lower case
       letters are to be differentiated. Each entry is to be separated from the
       next by a slash. Since the slash can thus not be used for structuring
       path names, the input of path names is not possible. All files and
       directories of this name within the share will be hidden. The names may
       include spaces and the wildcards ``*`` and ``?``.

       As an example, ``/.*/test/`` hides all files and directories the names of
       which begin with a *dot*, or which are called *test*.

       .. note::

          Entries in this field have an impact on the speed of Samba since every
          time particular contents of the share are to be displayed, all files
          and directories have to be checked according to the active filters.

   * - Postexec script
     - A script or command which is to be executed on the server if the
       connection to this share is finished.

   * - Preexec script
     - A script or command which is to be executed on the server each time a
       connection to this share is established.

.. _shares-management-samba-custom-settings-group:

Shares UMC module - Samba custom settings group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _shares-management-samba-custom-settings-group-table:

.. list-table:: *Samba custom settings* group
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Custom share settings
     - Apart from the properties which can, as a standard feature, be configured
       in a Samba share, this setting makes it possible to define further
       arbitrary Samba settings within the share. A list of available options
       can be obtained by the command :command:`man smb.conf`. In *Key* the name
       of the option is to be entered, and in the *Value* field the value to be
       set. Double entries of configuration options are not checked.

.. caution::

   The definition of extended Samba settings is only necessary in very special
   cases. The options should be thoroughly checked since they might have
   security-relevant effects.

.. _shares-management-options-tab:

Shares UMC module - Options tab
-------------------------------

.. _shares-management-options-tab-table:

.. list-table:: *Options* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Export for Samba clients
     - This option defines whether the share is to be exported for Samba
       clients.

   * - Export for NFS clients
     - This option defines whether the share is to be exported for NFS clients.
