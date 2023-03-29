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

.. _mail-virus:

Identification of viruses and malware
=====================================

The UCS mail services include virus and malware detection via the
:program:`univention-antivir-mail` package, which is automatically set up during
the setup of the mail server package. The virus scan can be deactivated with
the |UCSUCRV| :envvar:`mail/antivir`.

All incoming and outgoing emails are scanned for viruses. If the scanner
recognizes a virus, the email is sent to quarantine. That means that the email
is stored on the server where it is not accessible to the user. The original
recipient receives a message per email stating that this measure has been
taken. If necessary, the administrator can restore or delete this from the
:file:`/var/lib/amavis/virusmails/` directory. Automatic deletion is not
performed.

The :program:`AMaViSd-new` software serves as an interface between the mail
server and different virus scanners. The free virus scanner ClamAV is included
in the package and enters operation immediately after installation. The
signatures required for virus identification are procured and updated
automatically and free of charge by the Freshclam service.

Alternatively or in addition, other virus scanners can also be integrated in
AMaViS. Postfix and AMaViS need to be restarted following changes to the AMaViS
or ClamAV configuration.
