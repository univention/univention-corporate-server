
.. _users-passwords:

User password management
========================

Passwords which are difficult to guess and regular password changes are
an essential element of the system security of a UCS domain. The
following properties can be configured for users using a
*password policy*.

If Samba is used, the settings of the Samba domain object (see
:ref:`users-password-samba`) apply for logins to Window clients. The settings of
the Samba domain object and the policy should be set identically, otherwise
different password requirements will apply for logins to Windows and UCS
systems.

The password is saved in different attributes for every user saved in
the management system:

* The ``krb5Key`` attribute stores the Kerberos password.

* The ``userPassword`` attribute stores the Unix password (in other Linux
  distributions present in :file:`/etc/shadow`).

* The ``sambaNTPassword`` attribute stores the NT password hash used by Samba.

Password changes are always initiated via Kerberos, either in the UCS PAM
configuration or via Samba.

.. _password-policy:

.. figure:: /images/users_policy_password.*
   :alt: Configuring a password policy

   Configuring a password policy

History length
   The *history length* saves the last password hashes. These passwords can then
   not be used by the user as a new password when setting a new password. With a
   password history length of five, for example, five new passwords must be set
   before a password can be reused. If no password history check should be
   performed, the value must be set to ``0``.

   The passwords are not stored retroactively. Example: If ten passwords were
   stored, and the value is reduced to three, the oldest seven passwords will be
   deleted during the next password change. If then the value is increased
   again, the number of stored passwords initially remains at three, and is only
   increased by each password change.

Password length
   The *password length* is the minimum length in characters that a user
   password must comply with. If no value is entered here, the minimum size is
   eight characters. The default value of eight characters for password length
   is fixed, so it always applies if no policy is set and the *Override password
   check* checkbox is not ticked. This means it even applies if the
   *default-settings* password policy has been deleted.

   If no password length check should be performed, the value must be set to ``0``.

   A per server default can be configured via |UCSUCRV|
   :envvar:`password/quality/length/min`, which applies to users that are not
   subject to a *UDM password policy*. See the |UCSUCRV| description for
   details.

Password expiry interval
   A *password expiry interval* demands regular password changes. A password
   change is demanded during login to |UCSWEB|\ s, to Kerberos, on Windows
   clients and on UCS systems following expiry of the period in days. The
   remaining validity of the password is displayed in the user management under
   *Password expiry date* in the *Account* tab. If this input field is left
   blank, no password expiry interval is applied.

Password quality check
   If the option *Password quality check* is activated, additional checks -
   including dictionary checks - are performed for password changes in Samba,
   |UCSWEB|\ s and Kerberos.

   The configuration is done via |UCSUCR| and should occur on all login servers.
   The following checks can be enforced:

   * Minimum number of digits in the new password
     (:envvar:`password/quality/credit/digits`).

   * Minimum number of uppercase letters in the new password
     (:envvar:`password/quality/credit/upper`).

   * Minimum number of lowercase letters in the new password
     (:envvar:`password/quality/credit/lower`).

   * Minimum number of characters in the new password which are neither letters
     nor digits (:envvar:`password/quality/credit/other`).

   * Individual characters/digits can be excluded
     (:envvar:`password/quality/forbidden/chars`).

   * Individual characters/figures can be made compulsory
     (:envvar:`password/quality/required/chars`).

   * Standard Microsoft password complexity criteria can be applied
     (:envvar:`password/quality/mspolicy`). This can be done in addition to the
     :program:`python-cracklib` checks (value ``yes``) or instead of them
     (``sufficient``). See |UCSUCRV| description for details.
