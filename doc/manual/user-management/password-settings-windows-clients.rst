.. _users-password-samba:

Password settings for Windows clients when using Samba
======================================================

With the Samba domain object, one can set the password requirements for
logins to Windows clients in a Samba domain.

The Samba domain object is managed via the UMC module :guilabel:`LDAP
directory`. It can be found in the ``samba``
container below the LDAP base and carries the domain's NetBIOS name.

The settings of the Samba domain object and the policy (see :ref:`users-passwords`) should be set identically,
otherwise different password requirements will apply for logins to
Windows and UCS systems.

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Description

   * - Password length
     - The minimum number of characters for a user password.

   * - Password history
     - The latest password changes are saved in the form of hashes. These
       passwords can then not be used by the user as a new password when setting
       a new password. With a password history of five, for example, five new
       passwords must be set before a password can be reused.

   * - Minimum password age
     - The period of time set for this must have at least expired since the last
       password change before a user can reset their password again.

   * - Maximum password age
     - Once the saved period of time has elapsed, the password must be changed
       again by the user the next time they sign in. If the value is left blank,
       the password is infinitely valid.
