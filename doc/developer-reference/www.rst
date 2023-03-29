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

.. _chap-www:

************
Web services
************

.. index::
   single: web services
   see: apache; web services

.. _www-overview:

Extending the overview page
===========================

When users open ``http://localhost/`` or :samp:`http://{hostname}/` in a
browser, they are redirected to the UCS overview page.

Depending on the preferred language negotiated by the web browser the user is
either redirected to the German or English version. The overview page is split
between *Installed web services* and *Administration* entries.

The start page can be extended using |UCSUCR| variables. :samp:`{PACKAGE}` refers
to a unique identifier, typically the name of the package shipping the
extensions to the overview page. The configurable options are explained below:

* :envvar:`ucs/web/overview/entries/admin/PACKAGE/OPTION` variables extend the
  administrative section.

* :envvar:`ucs/web/overview/entries/service/PACKAGE/OPTION` variables extend the
  web services section.

To configure an extension of the overview page the following options must/can be
set using the pattern :envvar:`ucs/web/overview/entries/admin/PACKAGE/OPTION`\
``=*VALUE*`` (and likewise for services).

``link``
   defines a link to a URL representing the service (usually a web interface).

``label``
   specifies a title for an overview entry. The title can also be translated;
   for example ``label/de`` can be used for a title in German.

``description``
   configures a longer description of an overview entry. The description can
   also be translated; for example ``description/de`` can be used for a
   description in German. Should not exceed 60 characters, because of space
   limitations of the rendered box.

``icon``
   Optionally an icon can be displayed. Using ``icon``, either a filename or a
   URI can be provided. When specifying a filename, the name must be relative to
   the directory :file:`/var/www`, that is with a leading '/'. All file formats
   typically displayed by browsers can be used (for example PNG/JPG). All icons
   must be scaled to *50x50* pixels.

``priority``
   The display order can be specified using ``priority``. Depending on the
   values the entries are displayed in *lexicographical* order (i.e.
   ``100`` < ``50``).

