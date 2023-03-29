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

.. _shares-general:

*********************
File share management
*********************

UCS supports the central management of directory shares. A share registered via
the UMC module :guilabel:`Shares` is created on an arbitrary UCS server system
as part of the UCS domain replication.

Provision for accessing clients can occur via CIFS (supported by Windows/Linux
clients) and/or NFS (primarily supported by Linux/Unix). The NFS shares managed
in the UMC module can be mounted by clients both via NFSv3 and via NFSv4.

If a file share is deleted on a server, the shared files in the directory are
preserved.

To be able to use access control lists on a share, the underlying Linux file
system must support POSIX ACLs. In UCS the file systems ``ext4`` and ``XFS``
support POSIX ACLs. The Samba configuration also allows storing DOS file
attributes in extended attributes of the Unix file system. To use extended
attributes, the partition must be mounted using the mount option ``user_xattr``.

.. toctree::
   :caption: Chapter contents:

   access-rights
   umc
   msdfs
   quota
