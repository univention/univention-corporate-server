.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-access-authentication:

Administrative access and authentication
========================================

This page describes how administrators access a Nubus for UCS system.
It also describes how to control authentication for selected services.
It covers the local ``root`` account, SSH access,
and PAM authentication restrictions.

.. _system-administration-root-account:

Administrative access with the root account
-------------------------------------------

Every Nubus for UCS system has a ``root`` account
for complete administrative access.
The installer sets the password during installation.
Nubus for UCS doesn't store the root user in the LDAP directory,
but in the local account database.

To change the password for the ``root`` user,
run the :command:`passwd` command.
The command doesn't check the password length
or compare the new password with previously set passwords.

.. seealso::

   :ref:`deployment-initial-system-configuration-password`
      for information about setting the root password during installation.

.. _system-administration-ssh-login:

SSH sign-in to systems
----------------------

Nubus for UCS installs an SSH server by default.
SSH provides encrypted connections to remote hosts.
It verifies host identities with cryptographic host keys.
You can configure SSH root sign-in,
X11 forwarding,
and the SSH port in the *Univention Configuration Registry*.

By default,
SSH permits the privileged ``root`` user to sign in.
For example,
you can configure a newly installed system from a remote location
when no users exist yet.

* To allow only SSH key-based sign-in for the ``root`` user,
  place the public key on the remote system
  and run the command in :numref:`ssh-root-public-key-sign-in`.

  .. code-block:: console
     :caption: Allow only public-key SSH sign-in for root
     :name: ssh-root-public-key-sign-in

     $ ucr set sshd/permitroot=without-password

* To prohibit SSH sign-in for the ``root`` user,
  run the command in :numref:`ssh-root-disable-sign-in`.

  .. code-block:: console
     :caption: Prohibit SSH sign-in for root
     :name: ssh-root-disable-sign-in

     $ ucr set auth/sshd/user/root=no

To apply the SSH configuration changes,
restart the SSH service as shown in :numref:`ssh-service-restart`.

.. code-block:: console
   :caption: Restart the SSH service after configuration changes
   :name: ssh-service-restart

   $ systemctl restart ssh

.. _system-administration-ssh-login-x-forward:

X11 forwarding
~~~~~~~~~~~~~~

With X11 forwarding enabled,
users can run graphical programs on a remote computer.
They connect with the :command:`ssh -X TARGETHOST` command.
Replace ``TARGETHOST`` with the hostname of the remote system.

* To enable X11 forwarding over SSH,
  run the command in :numref:`ssh-x11-forwarding-enable`.

  .. code-block:: console
     :caption: Enable X11 forwarding over SSH
     :name: ssh-x11-forwarding-enable

     $ ucr set sshd/xforwarding=yes

* To turn off X11 forwarding over SSH,
  run the command in :numref:`ssh-x11-forwarding-disable`.

  .. code-block:: console
     :caption: Turn off X11 forwarding over SSH
     :name: ssh-x11-forwarding-disable

     $ ucr set sshd/xforwarding=no

To apply the SSH configuration changes,
restart the SSH service as shown in :numref:`ssh-service-restart`.

.. _system-administration-ssh-login-change-port:

Change the standard SSH port
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The standard SSH port is 22 over TCP.
Before you change the port,
make sure that the firewall allows connections to the new port.
Keep the current SSH session open
until you verify access through the new port.

To use a different port,
run the command in :numref:`ssh-port-change`.
Replace ``PORT`` with the TCP port number
that the SSH server uses for incoming connections.

.. code-block:: console
   :caption: Change the SSH port
   :name: ssh-port-change

   $ ucr set sshd/port=PORT

To apply the SSH configuration changes,
restart the SSH service as shown in :numref:`ssh-service-restart`.

To verify access through the new port,
open a new SSH session with the command in :numref:`ssh-port-verify`.
Replace ``USERNAME`` with your username
and ``HOSTNAME`` with the hostname of the remote system.

.. code-block:: console
   :caption: Verify SSH access through a custom port
   :name: ssh-port-verify

   $ ssh -p PORT USERNAME@HOSTNAME

.. _system-administration-pam:

Authentication with PAM
-----------------------

Nubus for UCS uses *Pluggable Authentication Modules* (PAM)
for authentication services.
PAM provides a common interface for sign-in methods.
Applications don't need changes for each method.

By default,
only the ``root`` user and members of the ``Domain Admins`` group can
sign in remotely through SSH and locally on a ``tty``.

To restrict access to a PAM service,
choose a service identifier from the list.
Replace the following placeholders:

* :samp:`{SERVICE}` with the service identifier.
* :samp:`{USERNAME}` with the username.
* :samp:`{GROUPNAME}` with the group name.

You can restrict access to these services:

* SSH with ``sshd``
* Sign-in on a ``tty`` with ``login``
* Remote sign-in with ``rlogin``
* PPP with ``ppp``
* Other services with ``other``

To restrict access to a service,
run the command in :numref:`pam-enable-service-restriction`.

.. code-block:: console
   :caption: Restrict access to a PAM service
   :name: pam-enable-service-restriction

   $ ucr set auth/SERVICE/restrict=yes

To grant access to a user,
run the command in :numref:`pam-grant-user-access`.

.. code-block:: console
   :caption: Grant user access to a PAM service
   :name: pam-grant-user-access

   $ ucr set auth/SERVICE/user/USERNAME=yes

To grant access to a group,
run the command in :numref:`pam-grant-group-access`.

.. code-block:: console
   :caption: Grant group access to a PAM service
   :name: pam-grant-group-access

   $ ucr set auth/SERVICE/group/GROUPNAME=yes

The commands in :numref:`pam-ssh-access-restrictions`
restrict SSH access to selected groups.

.. code-block:: console
   :caption: Restrict SSH access to selected groups
   :name: pam-ssh-access-restrictions

   $ ucr set "auth/sshd/group/Administrators=yes"
   $ ucr set "auth/sshd/group/Computers=yes"
   $ ucr set "auth/sshd/group/DC Backup Hosts=yes"
   $ ucr set "auth/sshd/group/DC Slave Hosts=yes"
   $ ucr set "auth/sshd/group/Domain Admins=yes"
   $ ucr set "auth/sshd/restrict=yes"
