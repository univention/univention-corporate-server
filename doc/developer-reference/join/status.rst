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

.. _join-status:

Join status
===========

.. index::
   single: domain join; join status

For each join script a version number is tracked. This is used to skip
re-executing join scripts, which already have been executed. This is mostly a
performance optimization, but is also used to find join scripts which need to be
run.

The text file :file:`/var/univention-join/status` is used to keep track of the
state of all join scripts. For each successful run of a join script a line is
appended to that file. That record consists of three space separated entries:

::

   $script_name v$version successful

#. The first entry contains the name of the join script without the two-digit
   prefix and without the :file:`.inst` suffix, usually corresponding to the
   package name.

#. The second entry contains a version number prefixed by a ``v``. It is used to
   keep track of the latest version of the join script, which has been run
   successfully. This is used to identify, which join scripts need to be
   executed and which can be skipped, because they were already executed in the
   past.

#. The third column contains the word successful.

If a new version of the join script is invoked, it just appends a new record
with a higher version number at the end of the file.
