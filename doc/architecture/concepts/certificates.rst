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

.. _concept-certificates:

Certificate infrastructure
==========================

The certificate infrastructure in a domain operated with |UCS| ensures the trust
context between all participants. The first domain node creates its own |CA| for
the domain. For more information, see the `Wikipedia article Certificate
authority <w-certificate-authority_>`_.

UCS uses |TLS|. The UCS Primary Directory Node creates the CA on behalf of the
domain during its installation and signs certificates for other systems that
join the domain. All certificates have an expiration date. Backup Directory
Nodes in the domain repeatedly pull all certificates from the Primary Domain
Controller to allow administrators to promote one of them to a Primary Directory
Node any time, if needed.

Services in the UCS domain also use the certificates created by UCS.
Administrators can configure alternative certificates for end-user or internet
facing services with certificates issued by third parties, for example `Let's
Encrypt <lets-encrypt_>`_.

.. TODO : Two reviewers provided feedback on this section and wanted to see
   links to UCR variables and more information. But the current detail level
   prohibits it at this point. Maybe a later section can refer to this part and
   at the same time also provide the interesting links. It would stay in the
   scope. See https://git.knut.univention.de/univention/ucs/-/merge_requests/358#note_62484

The domain systems use the certificates for secure communication between each
other over the computer network, for example for domain database replication and
the web interface of the UCS management system. Communication clients need to
know the public key of the domain's CA to validate the public key of the
certificate.
