.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _users-general:

***************
User management
***************

.. highlight:: console

UCS integrates central identity management. All user information are managed
centrally in UCS via the |UCSUMC| module :guilabel:`Users` and stored in the
LDAP directory service.

.. note::

   The user management is part of Univention Nubus in the *Directory Manager* component.
   For more information about Nubus, refer to :ref:`introduction-nubus`

All the services integrated in the domain access the central account
information, i.e., the same username and password are used for the user login to
a Windows client as for the login on the IMAP server.

The domain-wide management of user data reduces the administrative efforts as
changes do not need to be subsequently configured on different individual
systems. Moreover, this also avoids subsequent errors arising from
inconsistencies between the individual datasets.

.. _users-types:

.. rubric:: User account types

There are three different types of user accounts in UCS:

1. **Normal user accounts** have all available properties. These users can log
   in to UCS or Windows systems and, depending on the configuration, also to the
   installed Apps. The users can be administered via the UMC module
   :guilabel:`Users` (see :ref:`users-management`).

2. **Address book entries** can be used to maintain internal or external contact
   information. These contacts can't sign in to UCS or Windows systems.
   Address book entries can be managed via the UMC module :guilabel:`Contacts`.

3. **Simple authentication account**: With a simple authentication account, a
   user object is created, which has only a username and a password. With this
   account, only authentication against the LDAP directory service is possible,
   but no login to UCS or Windows systems. Simple authentication accounts can be
   accessed via the UMC module :guilabel:`LDAP directory` (see
   :ref:`central-navigation`).

.. _users-recommendation-usernames:

.. rubric:: Recommendation for username definition

One important and required attribute for user accounts is the *username*.
To avoid conflicts with different tools handling user accounts in UCS,
follow these recommendations for username definition:

* Use letters (``a-z`` and ``A-Z``),
  digits (``0-9``),
  dots (``.``),
  hyphens (``-``),
  and underscores (``_``)
  from the ASCII character set in usernames.
  Unicode characters and umlauts are also supported.

* The username must start with a letter, digit, or underscore and end with a letter, digit, or hyphen.

* Don't use spaces in usernames.

* Don't use ``@``, ``$``,
  or any of ``" / \ [ ] : ; | = , + * ? < >'`` in usernames.
  These characters cause failures with Kerberos, Active Directory,
  and Samba synchronization.

Recommended username length:

* For broad compatibility with Windows clients and legacy systems,
  keep usernames between 4 and 20 characters.
  While UCS allows single-character usernames,
  many external systems don't support them.

* Usernames longer than 20 characters cause problems in two situations:

  * Windows clients can't sign in,
    as the Microsoft specification limits the ``SAM account name`` to 20 characters.

  * Synchronization with an external Active Directory domain fails,
    as AD enforces the 20-character limit with a hard error.

  * The *Management UI* shows a warning when a username exceeds 20 characters.

The traditional recommendation follows this regular expression:
:regexp:`^[a-z][a-z0-9-]{2,18}[a-z0-9]$`.
This pattern is more restrictive than the actual system validation,
which also allows dots, underscores, and uppercase letters.

Treat the requirements listed before as guidelines for broad compatibility,
not as strict enforcement rules.
Keep potential side-effects in mind when defining usernames outside these guidelines,
especially for integration with legacy systems or Windows clients.

.. toctree::
   :caption: Chapter contents:

   umc
   user-activation-apps
   password-management
   password-settings-windows-clients
   user-self-service
   user-lockout
   user-templates
   last-bind-overlay
   udm-blocklists
   udm-recycle-bin
