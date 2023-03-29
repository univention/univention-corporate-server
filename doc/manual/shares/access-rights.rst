.. Like what you see? Join us!
.. https://www.univention.com/about-us/careers/vacancies/
..
.. Copyright (C) 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only
..
.. https://www.univention.com/
..
.. All rights reserved.
..
.. The source code of this program is made available under the terms of
.. the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
.. published by the Free Software Foundation.
..
.. Binary versions of this program provided by Univention to you as
.. well as other copyrighted, protected or trademarked materials like
.. Logos, graphics, fonts, specific documentations and configurations,
.. cryptographic keys etc. are subject to a license agreement between
.. you and Univention and not subject to the AGPL-3.0-only.
..
.. In the case you use this program under the terms of the AGPL-3.0-only,
.. the program is provided in the hope that it will be useful, but
.. WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
.. Affero General Public License for more details.
..
.. You should have received a copy of the GNU Affero General Public
.. License with the Debian GNU/Linux or Univention distribution in file
.. /usr/share/common-licenses/AGPL-3; if not, see
.. <https://www.gnu.org/licenses/agpl-3.0.txt>.

.. _shares-permissions:

Access rights to data in shares
===============================

Access permissions to files are managed in UCS using users and groups. All the
file servers in the UCS domain access identical user and group data via the LDAP
directory.

Three access rights are differentiated per file:

* read
* write
* execute

Three access rights also apply per directory: read and write are the same; the
execute permission here refers to the permission to enter a directory.

Each file/directory is owned by a user and a group. The three permission
outlined above can be applied to the user owner, the owner group and all others.

setuid
   If the *setuid* option is set for an executable file, it can be run by users
   with the privileges of the owner of the file.

setgid
   If the *setgid* option is set for a directory, files saved there inherit the
   directory's owner group. If further directories are created, they also
   inherit the option.

sticky bit
   If the *sticky bit* option is enabled for a directory, files in this
   directory can only be deleted by the owner of the file or the root user.

Access control lists allow even more complex permission models. The
configuration of ACLs is described in `SDB 1042 <univention-kb_>`_.

In the Unix permission model - and thus under UCS - write permission is not
sufficient to change the permissions of a file. This is limited to the
owner/owner group of a file. In contrast, under Microsoft Windows all users with
write permissions also have the permission to change the permissions. This
scheme can be adjusted for CIFS shares (see :ref:`shares-management`).

Only initial users and access permissions are assigned when a directory share is
created. If the directory already exists, the permissions of the existing
directory are adjusted.

Changes to the permissions of a shared directory performed directly in the file
system are not forwarded to the LDAP directory. If the permissions/owners are
edited with the UMC module :guilabel:`Shares`, the changes in the file system
are overwritten. Settings to the root directory of a file share should thus only
be set and edited with the UMC module. Additional adjustment of the access
permissions of the subordinate directories are then performed via the accessing
clients, e.g., via Windows Explorer, or directly via command line commands on
the file server.

The *homes* share plays a special role within Samba. This share is used for
sharing the home directories of the users. This share is automatically converted
to the user's home directory. Samba therefore ignores the rights assigned to the
share, and uses the rights of the respective home directory instead.
