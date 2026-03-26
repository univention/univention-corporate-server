.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _mail-management-general:

Management of the mail server data
==================================

.. _mail-management-domains:

Management of mail domains
--------------------------

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-mail-management`
in :cite:t:`uv-nubus-manual`.

.. _mail-management-users:

Assignment of email addresses to users
---------------------------------------

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-mail-users`
in :cite:t:`uv-nubus-manual`.

.. _mail-management-mailinglists:

Management of mailing lists
---------------------------

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-mail-mailinglists`
in :cite:t:`uv-nubus-manual`.

.. _mail-management-mailgroups:

Management of mail groups
-------------------------

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-mail-groups`
in :cite:t:`uv-nubus-manual`.

.. _mail-management-shared-folder:

Management of shared IMAP folders
---------------------------------

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-mail-shared-folders`
in :cite:t:`uv-nubus-manual`.

.. _mail-management-shared-folder-general-tab:

Shared IMAP folder - General tab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-mail-shared-folders-general-tab`
in :cite:t:`uv-nubus-manual`.

.. _mail-management-shared-folder-access-rights-tab:

Shared IMAP folder - Access rights tab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-mail-shared-folders-access-rights-tab`
in :cite:t:`uv-nubus-manual`.

.. _mail-quota:

Mail quota
----------

The size of the users' mailboxes can be restricted via the mail quota. When
this is attained, no further emails can be accepted for the mailbox by the mail
server until the user deletes old mails from their account.

The limit is specified in megabytes in the *Mail quota* field under
:menuselection:`Advanced settings --> Mail`. The default value is ``0`` and
means that no limit is set. The multi edit mode of UMC modules can be used to
assign a quota to multiple users at one time, see
:ref:`central-user-interface-edit`.

The user can be warned once a specified portion of the mailbox is attained and
then receives a message that their available storage space is almost full. The
administrator can enter the threshold in percent and the messages subject and
text:

* The threshold for when the warning message should be issued can be configured
  in the |UCSUCRV| :envvar:`mail/dovecot/quota/warning/text`, for example
  :samp:`mail/dovecot/quota/warning/text/{PERCENT}={TEXT}`

  ``PERCENT`` must be a number between 0 and 100 without the percent sign.

  ``TEXT`` will be the content of the email. If the value ``TEXT`` contains the
  string ``$PERCENT``, it will be replaced in the email with the value of the
  limit that has been exceeded.

  The value of the |UCSUCRV| :envvar:`mail/dovecot/quota/warning/subject` will
  be used for the subject of the email.

* When the mail server package is installed, a subject and two warning messages
  are automatically configured:

  * :envvar:`mail/dovecot/quota/warning/subject` is set to ``Quota-Warning``

  * :envvar:`mail/dovecot/quota/warning/text/80` is set to ``Your mailbox has
    filled up to over $PERCENT%.``

  * :envvar:`mail/dovecot/quota/warning/text/95` is set to ``Attention: Your
    mailbox has already filled up to over $PERCENT%. Please delete some messages
    or contact the administrator.``
