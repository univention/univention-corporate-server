.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _security-hardening-ssh:

Harden SSH access
=================

The Secure Shell (SSH) service provides remote administration access to UCS
systems.
Reduce its attack surface by using individual administrator accounts and SSH
keys, then disabling authentication methods and forwarding features that your
environment doesn't require.

For the basic SSH procedures, see :ref:`system-administration-ssh-login`.

.. warning::

   Keep the current administrative session open while changing SSH settings.
   Before disabling root or password sign-in, verify a separate account with
   administrative privileges and a local or console recovery path.

.. _security-hardening-ssh-authentication:

Restrict SSH authentication
----------------------------

Univention recommends using personalized administrator accounts with
public-key authentication.
Don't use ``root`` or a shared administrator account for daily work.
Use separate accounts for system and domain administration where the
operational model requires that separation.

To prohibit direct root sign-in, set the following UCR variable on each
affected system:

.. code-block:: console

   $ ucr set sshd/permitroot=no

If a controlled key-only root recovery path is required, use
``prohibit-password`` instead.
The value ``yes`` permits unrestricted root sign-in and increases the impact
of a compromised root credential.

To disable password authentication, set:

.. code-block:: console

   $ ucr set sshd/passwordauthentication=no

Deploy and test the SSH keys before applying this change.
Password authentication can still be required by automation or recovery
procedures, so check those dependencies first.

.. _security-hardening-ssh-forwarding:

Disable unused forwarding
-------------------------

X11 forwarding permits a remote client to forward graphical connections
through the SSH server.
If no administrative workflow requires it, disable it:

.. code-block:: console

   $ ucr set sshd/xforwarding=no

Restart SSH after changing the configuration:

.. code-block:: console

   $ systemctl restart ssh

The settings don't apply to an existing session.
Test a new session before closing the current one.

.. _security-hardening-ssh-timeouts:

Close inactive SSH sessions
----------------------------

The SSH server can close inactive sessions after it has sent keepalive
messages without receiving a response.
The default interval is 60 seconds and the default count is 3, resulting in a
timeout of about 3 minutes.
Configure both values together:

.. code-block:: console

   $ ucr set sshd/ClientAliveInterval=60
   $ ucr set sshd/ClientAliveCountMax=3

These settings don't close a session while a terminal multiplexer such as
:program:`screen` or :program:`tmux` remains active.
Choose values that protect unattended sessions without encouraging
administrators to use shared accounts or unsafe workarounds.

.. _security-hardening-ssh-cryptography:

Review SSH cryptography
-----------------------

UCS exposes the SSH cipher, message authentication code, and key-exchange
lists through the following UCR variables:

* :envvar:`sshd/Ciphers`
* :envvar:`sshd/MACs`
* :envvar:`sshd/KexAlgorithms`

Use the algorithms supported by the installed OpenSSH version and remove
algorithms that your security policy classifies as obsolete.
Don't copy a list from another system without testing client compatibility.
Keep SSH protocol version 2 enabled and don't enable protocol version 1.

Review host keys after upgrades or migrations.
If you create missing host keys, commit the SSH configuration so that the
daemon uses them:

.. code-block:: console

   $ ucr set sshd/HostKey/rsa=4096
   $ univention-openssh-recreate-host-keys
   $ ucr commit /etc/ssh/sshd_config

The :program:`univention-openssh-recreate-host-keys` command can create host
key types that an older installation doesn't have.
Review the host-key files and their permissions before committing the
configuration.

For key-generation procedures and supported key types, see the OpenSSH
documentation for the installed UCS release.
