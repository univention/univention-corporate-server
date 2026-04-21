.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _password-management-hashes:

Password hashes
===============

Understanding password hashing helps you secure user accounts and comply with security policies.
This page explains how Nubus for UCS hashes passwords and how to configure stronger hashing algorithms.

By default, Nubus for UCS uses SHA-512, which is secure for most environments.
If your security requirements are higher, you can enable bcrypt hashing for additional protection.

.. _password-management-hashes-sha512:

Default hashing method
----------------------

The directory service stores user password hashes in the ``userPassword`` attribute.
The :program:`crypt` library function hashes passwords.
You can configure the hashing method using the :term:`UCR variable`
:envvar:`password/hashing/method`.
The default value is ``SHA-512``.

.. _password-management-hashes-bcrypt:

bcrypt hashing method
---------------------

As an alternative,
Nubus for UCS offers :program:`bcrypt` as a hashing method for user account passwords.
To activate :program:`bcrypt`, you must complete the following steps.
If you don't complete these steps, you can't authenticate using a :program:`bcrypt` password hash.

#. Set the :term:`UCR variable` :envvar:`ldap/pw-bcrypt` to ``true`` on all LDAP servers.
#. Set the :term:`UCR variable` :envvar:`password/hashing/bcrypt` to ``true`` on all LDAP servers to activate :program:`bcrypt` as the hashing method for setting or changing user passwords.

.. caution::

   :program:`bcrypt` limits password length to a maximum of 72 characters.

.. _password-management-hashes-bcrypt-settings:

bcrypt settings
---------------

Configure the :program:`bcrypt` hashing settings to tune the security-performance balance.
These settings apply only to newly created password hashes.
Existing hashes retain their original algorithm and settings.

:envvar:`password/hashing/bcrypt/cost_factor`
   Sets the bcrypt cost factor
   and increases security by slowing down hashing. Default: ``12``.

:envvar:`password/hashing/bcrypt/prefix`
   Sets the bcrypt variant. Default: ``2b``.
