.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _deployment:

*****************
System deployment
*****************

This chapter describes installation procedures for Nubus for UCS across various deployment
environments.
As a technical administrator, you find detailed instructions for both traditional and cloud-based installation methods,
along with platform-specific considerations.

Required knowledge and skills
   * Basic understanding of system administration and networking, including IP addressing, DNS, and DHCP.
   * Familiarity with partitioning concepts and file system management.
   * Ability to configure domain settings and directory services.
   * Experience with virtualization platforms for relevant deployment scenarios.
   * Understanding of Active Directory integration if joining existing Windows domains.

What you learn
   * Step-by-step interactive installation through DVD for physical servers
     and DVD image for virtual machines.

   * Configuration options for BIOS and UEFI systems, including Secure Boot.

   * Network setup procedures for both automatic DHCP and manual IP configuration.

   * Hard drive partitioning strategies including LVM and encryption options.

   * Domain mode selection and system role configuration.

   * Alternative installation methods: text-mode, cloud-based Amazon EC2, and VMware-specific deployment.

   * Troubleshooting common installation issues.

Installation overview
   * Nubus for UCS divides the installation process into four main deployment paths,
     each suited to different infrastructure needs.

   * Choose the method that best matches your deployment environment,
     then follow the relevant subsections for step-by-step guidance.


.. toctree::

   install
   initial-system-configuration
   domain-setup
   after-installation
   trouble
