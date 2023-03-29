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
