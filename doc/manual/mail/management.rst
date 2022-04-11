.. _mail-management-general:

Management of the mail server data
==================================

.. _mail-management-domains:

Management of mail domains
--------------------------

A mail domain is an common namespace for e-mail addresses, mailing lists and
IMAP group folders. Postfix differentiates between the delivery of e-mails
between local and external domains. Delivery to mailboxes defined in the LDAP
directory is only conducted for e-mail address from local domains. The name of a
mail domain may only be composed of lowercase letters, the figures 0-9, full
stops and hyphens.

Several mail domains can be managed with UCS. The managed mail domains do not
need to be the DNS domains of the server - they can be selected at will. The
mail domains registered on a mail server are automatically saved in the
|UCSUCRV| :envvar:`mail/hosteddomains`.

To ensure that external senders can also send e-mails to members of the domain,
MX records must be created in the configuration of the authoritative name
servers, which designate the UCS server as mail server for the domain. These DNS
adjustments are generally performed by an Internet provider.

Mail domains are managed in the UMC module :guilabel:`Mail` with the
*Mail domain* object type.

.. _mail-management-users:

Assignment of e-mail addresses to users
---------------------------------------

A user can be assigned three different types of e-mail addresses:

Primary e-mail address
   The *primary e-mail address* is used for authentication on Postfix and
   Dovecot. Primary e-mail addresses must always be unique. Only one primary
   e-mail address can be configured for every user. It also defines the user's
   IMAP mailbox. If a mail home server is assigned to a user (see
   :ref:`mail-homeserver`), the IMAP inbox is automatically created by a
   |UCSUDL| module. The domain part of the e-mail address must be registered in
   the UMC module :guilabel:`Mail` (see :ref:`mail-management-domains`).

Alternative e-mail addresses
   E-mails to *alternative e-mail addresses* are also delivered to the user's
   mailbox. As many addresses can be entered as you wish. The alternative e-mail
   addresses do not have to be unique: if two users have the same e-mail
   address, they both receive all the e-mails which are sent to this address.
   The domain part of the e-mail address must be registered in the UMC module
   :guilabel:`Mail` (see :ref:`mail-management-domains`). To receive e-mails to
   alternative e-mail addresses, a user must have a primary e-mail address.

Forward e-mail addresses
   If *forward e-mail addresses* are configured for a user, e-mails received
   through the primary or alternative e-mail addresses are forwarded to them. A
   copy of the messages can optionally be stored in the user's mailbox. Forward
   e-mail addresses do not have to be unique and their domain part does not have
   to be registered via a UMC module.

.. note::

   E-mail addresses can consist of the following characters: letters ``a-z``,
   figures ``0-9``, dots (``.``), hyphens (``-``) and underscores (``_``). The
   address has to begin with a letter and must include an ``@`` character. At
   least one mail domain must be registered for to be able to assign e-mail
   addresses (see :ref:`mail-management-domains`).

E-mail addresses are managed in the UMC module :guilabel:`Users`. The *primary
e-mail address* is entered in the *General* tab in the *User account* submenu.
*Alternative e-mail addresses* can be entered under :menuselection:`Advanced
settings --> Mail`.

.. note::

   Once the user account is properly configured, authentication to the mail
   stack is possible (``IMAP``/``POP3``/``SMTP``). Please keep in mind that
   after disabling the account or changing the password, the login to the mail
   stack is still possible for 5 minutes due to the authentication cache of the
   mail stack. To invalidate the authentication cache run

   .. code-block:: console

      $ doveadm auth cache flush


   on the mail server. The expiration time of the authentication cache can be
   configured on the mail server with the |UCSUCRV|
   :envvar:`mail/dovecot/auth/cache_ttl` and
   :envvar:`mail/dovecot/auth/cache_negative_ttl`.

.. _mail-management-mailinglists:

Management of mailing lists
---------------------------

Mailing lists are used to exchange e-mails in closed groups. Each mailing list
has its own e-mail address. If an e-mail is sent to this address, it is received
by all the members of the mailing list.

.. _mail-mailinglist:

.. figure:: /images/mail_mailinglist.*
   :alt: Creating a mailing list

   Creating a mailing list

Mail domains are managed in the UMC module :guilabel:`Mail` with the *Mailing
list* object type. A name of your choice can be entered for the mailing list
under *Name*; the entry of a *Description* is optional. The e-mail address of
the mailing list should be entered as the *Mail address*. The domain part of the
address needs to be the same as one of the managed mail domains. As many
addresses as necessary can be entered under *Members*. In contrast to mail
groups (see :ref:`mail-management-mailgroups`), external e-mail addresses can
also be added here. The mailing list is available immediately after its
creation.

By default everyone can write to the mailing list. To prevent misuse, there is
the possibility of restricting the circle of people who can send mails. To do
so, the |UCSUCRV| :envvar:`mail/postfix/policy/listfilter` on the mail server
must be set to ``yes`` and Postfix restarted. *Users that are allowed to send
e-mails to the list* and *Groups that are allowed to send e-mails to the list*
can be specified under *Advanced settings*. If a field is set here, only
authorized users/groups are allowed to send mails.

.. _mail-management-mailgroups:

Management of mail groups
-------------------------

There is the possibility of creating a mail group: This is where an e-mail
address is assigned to a group of users. E-mails to this address are delivered
to the primary e-mail address of each of the group members.

Mail groups are managed in the UMC module :guilabel:`Groups` (see
:ref:`groups`).

The e-mail address of the mail group is specified in the *mail address* input
field under *Advanced settings*. The domain part of the address must be the same
as one of the managed mail domains.

By default everyone can write to the mail group. To prevent misuse, there is the
possibility of restricting the circle of people who can send mails. To do so,
the |UCSUCRV| :envvar:`mail/postfix/policy/listfilter` on the mail server must
be set to ``yes`` and Postfix restarted.

*Users that are allowed to send e-mails to the group* and *Groups that are
allowed to send e-mails to the group* can be specified under *Advanced
settings*. If a field is set here, only authorized users/groups are allowed to
send mails.

.. _mail-management-shared-folder:

Management of shared IMAP folders
---------------------------------

Shared e-mail access forms the basis for cooperation in many work groups. In
UCS, users can easily create folders in their own mailboxes and assign
permissions so that other users may read e-mails in these folders or save
additional e-mails in them.

Alternatively, individual IMAP folders can be shared for users or user groups.
This type of folder is described as a shared IMAP folder. Shared IMAP folders
are managed in the UMC module :guilabel:`Mail` with the *Mail folder (IMAP)*
object type.

Shared folders cannot be renamed, therefore the |UCSUCRV|
:envvar:`mail/dovecot/mailbox/rename` is not taken into account. When a shared
folder is deleted in the UMC module :guilabel:`Mail`, it is only deleted from
the hard disk, if :envvar:`mail/dovecot/mailbox/delete` is set to ``yes``. The
default value is ``no``.

.. _mail-shared-folder:

.. figure:: /images/mail_imapfolder.*
   :alt: Creating a shared IMAP folder

   Creating a shared IMAP folder

.. _mail-management-shared-folder-general-tab:

.. rubric:: Shared IMAP folder - General tab

.. _mail-management-shared-folder-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Name (*)
     - The name under which the IMAP folder is available in the e-mail clients.
       The name displayed in the IMAP client differs depending on if an e-mail
       address is configured (see field *E-Mail address*) or not. If no
       e-mail address is configured, the IMAP folder will be displayed in the
       client as ``name@domain/INBOX``. If an e-mail address is configured, it
       will be ``shared/name@domain``.

   * - Mail domain (*)
     - Every shared IMAP folder is assigned to a mail domain. The management of
       the domains is documented in the :ref:`mail-management-domains`.

   * - Mail home server (*)
     - An IMAP folder is assigned to a mail home server. Further information can
       be found in :ref:`mail-homeserver`.

   * - Quota in MB
     - This setting can be used to set the maximum total size of all e-mails in
       this folder.

   * - E-Mail address
     - An e-mail address can be entered here via which e-mails can be sent
       directly to the IMAP folder. If no address is set here, it is only
       possible to write in the folder from e-mail clients.

       The domain part of the e-mail address must be registered in the UMC
       module :guilabel:`Mail` (see :ref:`mail-management-domains`).

.. _mail-management-shared-folder-access-rights-tab:

.. rubric:: Shared IMAP folder - Access rights tab

.. _mail-management-shared-folder-access-rights-tab-table:

.. list-table:: *Access rights* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Name (*)
     - Access permissions based on users or groups can be entered here. Users
       are entered with their user name; the groups saved in the UMC module
       :guilabel:`Groups` can be used as groups.

       The access permissions have the following consequences for individual
       users or members of the specified group:

       No access
          No access is possible. The folder is not displayed in the folder list.

       Read
          The user may only perform read access to existing entries.

       Append
          Existing entries may not be edited; only new entries may be created.

       Write
          New entries may be created in this directory; existing entries may be
          edited or deleted.

       Post
          Sending an e-mail to this directory as a recipient is permitted. This
          function is not supported by all the clients.

       All
          Encompasses all permissions of *write* and also allows the changing of
          access permissions.

.. _mail-quota:

Mail quota
----------

The size of the users' mailboxes can be restricted via the mail quota.  When
this is attained, no further e-mails can be accepted for the mailbox by the mail
server until the user deletes old mails from her account.

The limit is specified in megabytes in the *Mail quota* field under
:menuselection:`Advanced settings --> Mail`. The default value is ``0`` and
means that no limit is set. The multi edit mode of UMC modules can be used to
assign a quota to multiple users at one time, see
:ref:`central-user-interface-edit`.

The user can be warned once a specified portion of the mailbox is attained and
then receives a message that his available storage space is almost full. The
administrator can enter the threshold in percent and the messages subject and
text:

* The threshold for when the warning message should be issued can be configured
  in the |UCSUCRV| :envvar:`mail/dovecot/quota/warning/text`, for example
  :samp:`mail/dovecot/quota/warning/text/{PERCENT}={TEXT}`

  ``PERCENT`` must be a number between 0 and 100 without the percent sign.

  ``TEXT`` will be the content of the e-mail. If the value ``TEXT`` contains the
  string ``$PERCENT``, it will be replaced in the email with the value of the
  limit that has been exceeded.

  The value of the |UCSUCRV| :envvar:`mail/dovecot/quota/warning/subject` will
  be used for the subject of the e-mail.

* When the mail server package is installed, a subject and two warning messages
  are automatically configured:

  * ``mail/dovecot/quota/warning/subject`` is set to ``Quota-Warning``

  * ``mail/dovecot/quota/warning/text/80`` is set to ``Your mailbox has
    filled up to over $PERCENT%.``

  * ``mail/dovecot/quota/warning/text/95`` is set to ``Attention: Your
    mailbox has already filled up to over $PERCENT%. Please delete some messages
    or contact the administrator.``
