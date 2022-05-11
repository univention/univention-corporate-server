.. _domain-password-hashes:

Password hashes in the directory service
========================================

User password hashes are stored in the directory service in the ``userPassword``
attribute. The :program:`crypt` library function is used to hash passwords. The
actual hashing method can be configured via the |UCSUCRV|
:envvar:`password/hashing/method`, ``SHA-512`` is used by default.

As an alternative |UCSUCS| (from version :uv:erratum:`4.4x887` on) offers the
option of using :program:`bcrypt` as hashing method for passwords of user
accounts. To activate :program:`bcrypt` support in OpenLDAP the |UCSUCRV|
:envvar:`ldap/pw-bcrypt` has to bet set to ``true`` on all LDAP servers.
Otherwise it is not possible authenticate with a :program:`bcrypt` hash as
password hash. Additionally the |UCSUCRV| :envvar:`password/hashing/bcrypt` has
to be set to ``true``, again on all servers, to activate :program:`bcrypt` as
the hashing method for setting or changing user password.

In addition, the :program:`bcrypt` cost factor and the
:program:`bcrypt` variant can be configured via the
|UCSUCRV|\ s :envvar:`password/hashing/bcrypt/cost_factor` (default
``12``) and :envvar:`password/hashing/bcrypt/prefix` (default ``2b``).

.. caution::

   :program:`bcrypt` is limited to a maximum of 72 characters. So only the first
   72 characters of the password are used to generate the hashes.
