.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _security-hardening-kerberos:

Harden password attributes and Kerberos keys
============================================

Nubus stores password-related attributes for different authentication protocols and services.

You can reduce the amount of legacy credential material in the directory service
by deactivating NT hash generation and restricting the Kerberos encryption types.
This page describes the required checks, configuration, and cleanup.

.. warning::

   Don't apply these settings before checking the integrations in your environment.

   Existing users and service accounts can continue to contain the affected values
   until you run the cleanup commands.

   After cleanup, you can't restore the removed values
   without resetting the affected passwords.

.. _security-hardening-kerberos-compatibility:

Choose hardening measures
-------------------------

The controls are independent:

* :envvar:`password/samba/nthash` controls whether Univention Directory
  Manager (UDM) generates ``sambaNTPassword`` when a password changes.

* :envvar:`kerberos/defaults/enctypes/permitted` controls the encryption types
  that UCS permits for Kerberos keys.

Changing either UCR variable doesn't remove values that already exist.
Use the cleanup procedures in :ref:`security-hardening-kerberos-cleanup`
for existing environments.

Disabling ``sambaNTPassword`` isn't possible in environments where one of the
following services uses NT hashes for core functionality:

S4/AD Connector
   Password synchronization between UCS and Active Directory requires the NT
   hash.

``univention-squid``
   The ``squid_ldap_ntlm_auth`` authentication backend requires the NT hash
   for transparent proxy authentication.

``univention-radius``
   The ``univention-radius-ntlm-auth`` helper requires the NT hash for
   MS-CHAP and NTLM authentication.

If one of these services is active, keep
:envvar:`password/samba/nthash` enabled.
Removing existing NT hashes breaks the affected authentication or
synchronization function and isn't reversible without resetting passwords.

Removing weak or deprecated encryption types from ``krb5Key`` can prevent a
principal from authenticating when a client or service supports only a
removed type.
This includes legacy Windows clients, old trusts, and service accounts that
haven't been migrated to AES encryption.
Check the encryption types used by domain integrations before proceeding.

.. _security-hardening-kerberos-attributes:

Credential attributes
---------------------

The directory service contain several password representations
because different services use different authentication protocols.
The following password representations are relevant for Kerberos:

``sambaNTPassword``
   An unsalted NT hash that supports legacy NTLM-based authentication.
   The hash isn't required for Kerberos authentication.

``krb5Key``
   Kerberos keys for a principal.
   A principal can have several keys so that clients and services
   that use different encryption types can authenticate during a migration.
   The attribute can contain keys that use encryption types
   that are insecure or deprecated.

``userPassword``
   The attribute contains a crypt hash
   that uses a configurable hashing method.
   For more information,
   see :ref:`password-management-hashes`.

.. _security-hardening-kerberos-configure:

Deactivate NT hash generation
-----------------------------

The following settings reduce legacy credential storage while preserving the
current UCS default behavior for services that need it.

If no active service requires NTLM-based authentication or password
synchronization, set the UCR variable on every system that runs UDM password
changes:

.. code-block:: console

   $ ucr set password/samba/nthash=false

UDM then stops generating ``sambaNTPassword`` during password changes and
removes the value when the password changes next.
The setting doesn't remove existing values immediately.

The cleanup scripts remove values from all matching directory objects.
Always create and verify a directory backup before running them.
Run the dry-run mode first to see which objects the command would change.

.. _security-hardening-kerberos-remove-nt-hashes:
.. _security-hardening-kerberos-cleanup:

Remove existing NT hashes
~~~~~~~~~~~~~~~~~~~~~~~~~

First verify that :envvar:`password/samba/nthash` is set to ``false`` on the
system from which you run the command.
Then run:

.. code-block:: console

   $ /usr/share/univention-directory-manager-tools/remove_sambantpassword --dry-run

If the output contains only accounts that you have approved for cleanup, run
the command without ``--dry-run``:

.. code-block:: console

   $ /usr/share/univention-directory-manager-tools/remove_sambantpassword

The command removes ``sambaNTPassword`` from all matching accounts.
It prints a warning when the UCR variable isn't set to ``false``.

.. _security-hardening-kerberos-restrict-encryption-types:

Restrict Kerberos encryption types
----------------------------------

To permit only AES-256 and AES-128 keys, set the following UCR variable on
each UCS system that provides or manages Kerberos credentials:

.. code-block:: console

   $ ucr set kerberos/defaults/enctypes/permitted='aes256-cts-hmac-sha1-96 aes128-cts-hmac-sha1-96'

This setting excludes the following types that are insecure or deprecated in
the default key set:

* ``arcfour-hmac-md5`` (also known as ``rc4-hmac``).
* ``des-cbc-crc``.
* ``des-cbc-md5``.
* ``des-cbc-md4``.
* ``des3-hmac-sha1`` and ``des3-cbc-sha1``.

The setting affects newly generated keys and Kerberos negotiation.
It doesn't remove weak keys that are already stored in ``krb5Key``.

.. caution::

   Test domain joins, trusts, service accounts, and applications after
   changing the permitted encryption types.
   If a required principal has no mutually supported encryption type, its
   authentication fails.

.. _security-hardening-kerberos-remove-weak-keys:

Remove weak Kerberos keys
~~~~~~~~~~~~~~~~~~~~~~~~~

The Kerberos cleanup command removes the default set of weak and deprecated
key types listed in the preceding section.
Run the dry-run mode first:

.. code-block:: console

   $ /usr/share/univention-directory-manager-tools/remove_krb5key_keytypes --dry-run

If the result is compatible with your environment, run:

.. code-block:: console

   $ /usr/share/univention-directory-manager-tools/remove_krb5key_keytypes

The command increments ``krb5KeyVersionNumber`` for changed objects.
If a ``krb5Key`` value can't be decoded, the command skips that object instead
of modifying it.

To remove a specific key type, use ``--keytype``.
You can specify the option multiple times.
The argument accepts a Kerberos key type name or an enctype ID.
For example, the following command removes RC4-HMAC keys only:

.. code-block:: console

   $ /usr/share/univention-directory-manager-tools/remove_krb5key_keytypes --keytype rc4-hmac

The cleanup is irreversible without resetting the affected account
passwords.

.. _security-hardening-kerberos-verify:

Verify the result
-----------------

After cleanup, verify authentication for:

* A regular user through the services that the user accesses.
* Every service account that runs an application or scheduled task.
* Domain joins, trusts, and Active Directory integrations, if configured.
* Proxy and RADIUS authentication, if those services are configured.

Read the relevant service log files for authentication failures.
If a required account can no longer authenticate, restore the affected
service from the backup or reset the account password to generate supported
keys again.

Related information
-------------------

For more information about Kerberos architecture in Nubus for UCS, see
:ref:`domain-infrastructure-kerberos`.
For information about password hashes, see
:ref:`password-management-hashes`.
