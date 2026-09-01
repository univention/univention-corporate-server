.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _security-hardening:

******************
Security hardening
******************

Security hardening reduces the likelihood and impact of attacks against a
Nubus for UCS environment.
It doesn't replace a risk assessment, network segmentation, backups, patch
management, monitoring, or physical security.

The recommendations in this chapter are grouped by component.
Apply only the recommendations that match the services and clients in your
environment.
Settings that improve security can also reduce compatibility or availability,
particularly when they disable legacy protocols.

Before changing a setting, record its current value, verify that you have a
recovery path, and test the change with the clients and integrations that you
operate.
Apply changes consistently to all systems that provide the affected service.

Use different passwords for the local ``root`` account and domain
administrator accounts.
Use a different local ``root`` password on each system to limit lateral
movement after a single system is compromised.
Use unprivileged, personal accounts for daily work and privileged accounts
only for administrative tasks.

The following pages cover the main components:

* :ref:`security-hardening-kerberos` covers password attributes and Kerberos
  encryption types.
* :ref:`security-hardening-samba` covers SMB, NetBIOS, and Samba services.

For account password policies and account lockout, see
:ref:`password-management-policies` and
:ref:`iam-user-lockout`.

.. toctree::
   :caption: Contents

   kerberos
   samba
