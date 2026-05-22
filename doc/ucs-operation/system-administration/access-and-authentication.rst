.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-access-authentication:

Administrative access and authentication
========================================

This page describes how to access a Nubus for UCS system for administrative tasks
and how to control authentication for selected services.
It covers the local ``root`` account, SSH access, and PAM-based authentication restrictions.

.. _system-administration-root-account:

Administrative access with the root account
-------------------------------------------

There is a ``root`` account on every UCS system for complete administrative
access. The password is set during installation of the system. The root user
**is not** stored in the LDAP directory, but instead in the local user accounts.

The password for the root user can be changed via the command line by using the
:command:`passwd` command. It must be pointed out that this process does not
include any checks regarding either the length of the password or the passwords
used in the past.

.. _system-administration-ssh-login:

SSH login to systems
--------------------

When installing a UCS system, an SSH server is also installed per preselection.
SSH is used for realizing encrypted connections to other hosts, wherein the
identity of a host can be assured via a check sum. Essential aspects of the SSH
server's configuration can be adjusted in *Univention Configuration Registry*.

By default the login of the privileged ``root`` user is permitted by SSH (e.g.
for configuring a newly installed system where no users have been created yet,
from a remote location).

* If the :term:`UCR variable` :envvar:`sshd/permitroot` is set to ``without-password``,
  then no interactive password request will be performed for the ``root`` user,
  but only a login based on a public key. By this means brute force attacks to
  passwords can be avoided.

* To prohibit SSH login completely, this can be deactivated by setting the
  UCR variable :envvar:`auth/sshd/user/root` to ``no``.

The UCR variable :envvar:`sshd/xforwarding` can be used to configure
whether an X11 output should be passed on via SSH. This is necessary,
for example, for allowing a user to start a program with graphic output
on a remote computer by logging in with :command:`ssh -X
TARGETHOST`. Valid settings are ``yes`` and
``no``.

The standard port for SSH connections is port 22 via TCP. If a different
port is to be used, this can be arranged via the UCR variable
:envvar:`sshd/port`.

.. _system-administration-pam:

Authentication / PAM
--------------------

Authentication services in Univention Corporate Server are realized via
*Pluggable Authentication Modules* (PAM). To this
end different login procedures are displayed on a common interface so
that a new login method does not require adaptation for existing
applications.

By default only the ``root`` user and members of the ``Domain Admins`` group can
login remotely via SSH and locally on a ``tty``.

This restriction can be configured with the :term:`UCR variable`
:samp:`auth/{SERVICE}/restrict`. Access to this service can be authorized by
setting the variables :samp:`auth/{SERVICE}/user/{USERNAME}` and
:samp:`auth/{SERVICE}/group/{GROUPNAME}` to ``yes``.

Login restrictions are supported for *SSH* (``sshd``), login on a *tty*
(``login``), *rlogin* (``rlogin``), *PPP* (``ppp``) and other services
(``other``). An example for *SSH*:

.. code-block::

   auth/sshd/group/Administrators: yes
   auth/sshd/group/Computers: yes
   auth/sshd/group/DC Backup Hosts: yes
   auth/sshd/group/DC Slave Hosts: yes
   auth/sshd/group/Domain Admins: yes
   auth/sshd/restrict: yes

