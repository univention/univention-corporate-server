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

.. _mail-spam:

Spam detection and filtering
============================

Undesirable and unsolicited emails are designated as spam. The software
SpamAssassin and Postgrey are integrated in UCS for the automatic identification
of these emails. SpamAssassin attempts to identify whether an email is
desirable or not based on heuristics concerning its origin, form and content.
Postgrey is a policy server for Postfix, which implements gray listing. Grey
listing is a spam detection method which denies the first delivery attempt of
external mail servers. Mail servers of spam senders most often do not perform a
second delivery attempt, while legitimate servers do so. Integration occurs via
the packages :program:`univention-spamassassin` and
:program:`univention-postgrey`, which are automatically set up during the
installation of the mail server package.

SpamAssassin operates a point system, which uses an increasing number of points
to express a high probability of the email being spam. Points are awarded
according to different criteria, for example, keywords within the email or
incorrect encodings. In the standard configuration only mails with a size of up
to 300 kilobytes are scanned, this can be adjusted using the |UCSUCRV|
:envvar:`mail/antispam/bodysizelimit`.

E-mails which are classified as spam - because they exceed a certain number of
points - are not delivered to the recipient's inbox by Dovecot, but rather in
the *Spam* folder below it. The name of the folder for spam can be configured
with the |UCSUCRV| :envvar:`mail/dovecot/folder/Spam`. The filtering is
performed by a Sieve script, which is automatically generated when the user is
created.

The threshold in these scripts as of which emails are declared to be spam can
be configured with the |UCSUCRV| :envvar:`mail/antispam/requiredhits`. The
presetting (``5``) generally does not need to be adjusted. However, depending
on experience in the local environment, this value can also be set lower. This
will, however, result in more emails being incorrectly designated as spam.
Changes to the threshold do not apply to existing users.

There is also the possibility of evaluating emails with a Bayes classifier.
This compares an incoming email with statistical data already gathered from
processed emails and uses this to adapt it's evaluation to the user's email.
The Bayes classification is controlled by the user himself, whereby emails not
identified as spam by the system can be placed in the *Spam* subfolder by the
user and a selection of legitimate emails copied into the *Ham*
(:envvar:`mail/dovecot/folder/ham`) subfolder. This folder is evaluated daily
and data which have not yet been collected or were previously classified
incorrectly are collected in a shared database. This evaluation is activated by
default and can be configured with the |UCSUCRV|
:envvar:`mail/antispam/learndaily`.

The spam filtering can be deactivated by setting the |UCSUCRV|
:envvar:`mail/antivir/spam` to ``no``. When modifying Univention Configuration
Registry variables concerning spam detection, the AMaViS service and Postfix
must be restarted subsequently.
