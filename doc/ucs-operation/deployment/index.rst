.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _deployment:

*****************
System deployment
*****************

This chapter describes how to install Nubus for UCS
across physical servers, virtual machines, and cloud environments.
It covers everything from choosing an installation method
through the first steps after the system is running.

Installation methods
   Choose the installation method that matches your environment:
   interactive DVD installation for physical and virtual machines,
   text mode for systems without graphical support,
   Amazon EC2 for cloud deployments,
   or VMware-specific configuration for VMware environments.
   See :ref:`deployment-installation-methods`.

Initial system configuration
   Work through the interactive installer to configure language, keyboard layout,
   network settings, disk partitioning, and the ``root`` password.
   See :ref:`deployment-initial-system-configuration`.

Domain setup
   Select a domain mode to complete the installation:
   create a Nubus for UCS domain, join an existing Nubus for UCS domain,
   or join an existing Active Directory domain.
   See :ref:`deployment-domain-setup`.

Steps after the installation
   Access the *Portal* and complete the first essential tasks
   after the installation finishes.
   See :ref:`deployment-after-installation`.

Troubleshooting
   Resolve common installation problems.
   See :ref:`deployment-installation-troubleshooting`.

.. toctree::
   :caption: Contents

   install
   initial-system-configuration
   domain-setup
   after-installation
   trouble
