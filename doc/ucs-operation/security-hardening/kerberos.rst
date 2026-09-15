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

.. _security-hardening-kerberos-attributes:

Credential attributes
---------------------

The directory service contains several password representations
because different services use different authentication protocols.
The following password representations are relevant for Kerberos:

.. _security-hardening-kerberos-attributes-sambantpassword:

``sambaNTPassword``
   An unsalted password hash that supports legacy NTLM-based authentication.
   The hash isn't required for Kerberos authentication.

.. _security-hardening-kerberos-attributes-krb5key:

``krb5Key``
   Stores Kerberos keys for a principal.
   A principal can have several keys with different encryption types.
   This supports authentication by clients and services during a migration.
   The attribute can contain insecure or deprecated keys.

.. _security-hardening-kerberos-attributes-userpassword:

``userPassword``
   Stores a crypt hash that uses a configurable hashing method.
   For more information about password hashes,
   see :ref:`password-management-hashes`.

.. _security-hardening-kerberos-compatibility:

Choose hardening measures
-------------------------

Before choosing a hardening measure,
identify the services in your environment that depend on NT hashes
or specific Kerberos encryption types.
You can apply the following controls independently:

:envvar:`password/samba/nthash`
   Controls whether :term:`Univention Directory Manager (UDM)` generates
   :ref:`security-hardening-kerberos-attributes-sambantpassword`
   when a password changes.

:envvar:`kerberos/defaults/enctypes/permitted`
   controls the encryption types
   that Univention Corporate Server (UCS) permits for Kerberos keys.

Changing either :term:`UCR variable` doesn't remove values that already exist.
For existing environments, use :ref:`security-hardening-kerberos-remove-nt-hashes`
or :ref:`security-hardening-kerberos-remove-weak-keys`.

You can't deactivate :ref:`security-hardening-kerberos-attributes-sambantpassword` in environments where one of the
following services uses NT hashes for core functionality:

Active Directory Connection
   Password synchronization between UCS and Active Directory requires the NT
   hash.

:program:`univention-squid`
   The ``squid_ldap_ntlm_auth`` authentication backend requires the NT hash
   for transparent proxy authentication.

:program:`univention-radius`
   The ``univention-radius-ntlm-auth`` helper requires the NT hash for
   MS-CHAP and NTLM authentication.

If one of these services is active, keep
:envvar:`password/samba/nthash` enabled.
Removing existing NT hashes breaks the affected authentication or
synchronization function and isn't reversible without resetting passwords.

Removing weak or deprecated encryption types from
:ref:`security-hardening-kerberos-attributes-krb5key`
can prevent a principal from authenticating
when a client or service supports only a removed type.
This includes legacy Windows clients,
service accounts that haven't migrated to AES encryption,
and trusts that support only removed encryption types.
Check the encryption types used by domain integrations before proceeding.

.. _security-hardening-kerberos-configure:

Deactivate NT hash generation
-----------------------------

To stop :term:`UDM` from generating
:ref:`security-hardening-kerberos-attributes-sambantpassword`
for future password changes,
change the :envvar:`password/samba/nthash` UCR variable.

If no active service requires NTLM-based authentication or password synchronization,
as outlined in :ref:`security-hardening-kerberos-compatibility`,
set the UCR variable on every system
that performs password changes through UDM.
Use the command in :numref:`security-hardening-kerberos-configure-listing`.
UDM then stops generating :ref:`security-hardening-kerberos-attributes-sambantpassword` during password changes and
removes the value when the password changes next.
The setting doesn't remove existing values immediately.

.. code-block:: console
   :caption: Deactivate NT hash generation
   :name: security-hardening-kerberos-configure-listing

   $ ucr set password/samba/nthash=false

.. _security-hardening-kerberos-remove-nt-hashes:

Remove existing NT hashes
~~~~~~~~~~~~~~~~~~~~~~~~~

The cleanup script remove values from all matching directory objects.
Before running it, create, and verify a directory backup as described in
:ref:`domain-infrastructure-ldap-directory-backup`.
Run the dry-run mode first to see which objects the command would change.

On the system from which you run the command,
verify that :envvar:`password/samba/nthash` has the value ``false``.
Then run the command in :numref:`security-hardening-kerberos-remove-nt-hashes-dry-run-remove-password-listing`.

.. code-block:: console
   :caption: Verify the accounts for removal of NT hashes
   :name: security-hardening-kerberos-remove-nt-hashes-dry-run-remove-password-listing

   $ /usr/share/univention-directory-manager-tools/remove_sambantpassword --dry-run

If the dry-run output lists only affected user accounts,
and you have approved them for cleanup,
run the command without ``--dry-run``,
as shown in :numref:`security-hardening-kerberos-remove-nt-hashes-remove-password-listing`.
The command removes :ref:`security-hardening-kerberos-attributes-sambantpassword` from all affected user accounts.
It prints a warning when the UCR variable isn't set to ``false``.

.. code-block:: console
   :caption: Remove NT hashes from matching accounts.
   :name: security-hardening-kerberos-remove-nt-hashes-remove-password-listing

   $ /usr/share/univention-directory-manager-tools/remove_sambantpassword

.. _security-hardening-kerberos-restrict-encryption-types:

Restrict Kerberos encryption types
----------------------------------

To permit only AES-256 and AES-128 keys,
set the :envvar:`kerberos/defaults/enctypes/permitted` UCR variable on each UCS system
that provides or manages Kerberos credentials,
as shown in :numref:`security-hardening-kerberos-restrict-encryption-types-listing`.

.. code-block:: console
   :caption: Restrict permitted Kerberos encryption types
   :name: security-hardening-kerberos-restrict-encryption-types-listing

   $ ucr set kerberos/defaults/enctypes/permitted='aes256-cts-hmac-sha1-96 aes128-cts-hmac-sha1-96'

This setting excludes the following types
that are insecure or deprecated in the default key set:

* ``arcfour-hmac-md5``, also known as ``rc4-hmac``
* ``des-cbc-crc``
* ``des-cbc-md5``
* ``des-cbc-md4``
* ``des3-hmac-sha1`` and ``des3-cbc-sha1``

The setting affects newly generated keys and Kerberos negotiation.
It doesn't remove weak keys that are already stored in
:ref:`security-hardening-kerberos-attributes-krb5key`.

.. caution::

   After changing the permitted encryption types,
   test domain joins, trusts, service accounts, and applications.
   If a required principal has no mutually supported encryption type,
   its authentication fails.

.. _security-hardening-kerberos-remove-weak-keys:

Remove weak Kerberos keys
~~~~~~~~~~~~~~~~~~~~~~~~~

The Kerberos cleanup command removes the default set of weak and deprecated
key types listed in :ref:`security-hardening-kerberos-restrict-encryption-types`.
Run the dry-run mode first,
as shown in :numref:`security-hardening-kerberos-remove-weak-keys-dry-run-listing`.

.. code-block:: console
   :caption: Identify weak Kerberos keys
   :name: security-hardening-kerberos-remove-weak-keys-dry-run-listing

   $ /usr/share/univention-directory-manager-tools/remove_krb5key_keytypes --dry-run

If no client, service, or domain integration requires the key types
in the dry-run output,
run the command shown in :numref:`security-hardening-kerberos-remove-weak-keys-listing`.
The command increments ``krb5KeyVersionNumber``
on each object that it changes.
If a :ref:`security-hardening-kerberos-attributes-krb5key` value can't be decoded,
the command skips that object instead of modifying it.

.. code-block:: console
   :caption: Remove weak Kerberos keys
   :name: security-hardening-kerberos-remove-weak-keys-listing

   $ /usr/share/univention-directory-manager-tools/remove_krb5key_keytypes

To remove a specific key type, use the command in
:numref:`security-hardening-kerberos-remove-weak-keys-key-type-listing`.
You can specify the ``--keytype`` option multiple times.
The argument accepts a Kerberos key type name or an enctype ID.
For example, specify ``rc4-hmac`` to remove only RC4-HMAC keys,
as shown in :numref:`security-hardening-kerberos-remove-weak-keys-key-type-listing`.

You can't reverse this cleanup
without resetting the affected account passwords.

.. code-block:: console
   :caption: Remove a specific Kerberos key type
   :name: security-hardening-kerberos-remove-weak-keys-key-type-listing

   $ /usr/share/univention-directory-manager-tools/remove_krb5key_keytypes --keytype rc4-hmac

.. _security-hardening-kerberos-verify:

Verify the result
-----------------

After cleanup, verify the following authentication paths:

* A regular user's access to the services that they use.
* Each service account that runs an application or scheduled task.
* Each configured domain join, trust, and Active Directory integration.
* Each configured proxy or RADIUS authentication service.

UDM then stops generating :ref:`security-hardening-kerberos-attributes-sambantpassword` during password changes.
The next time a password changes,
UDM removes :ref:`security-hardening-kerberos-attributes-sambantpassword`.
The setting doesn't remove existing values immediately.

.. _security-hardening-kerberos-related-information:

Related information
-------------------

For more information about Kerberos architecture in Nubus for UCS,
see :ref:`domain-infrastructure-kerberos`.

For information about password hashes,
see :ref:`password-management-hashes`.
