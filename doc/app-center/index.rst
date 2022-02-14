************
Introduction
************

This document is for app providers who want to place their product
clearly visible for a broad, professional and growing user group. It
covers the steps on how to make the product available as an app for
|UCSAPPC|.

.. _introduction:start:

What is |UCSAPPC|?
==================

|UCSAPPC| is an ecosystem similar to the app stores known from mobile
platforms like Apple or Google. It provides an infrastructure to build,
deploy and run enterprise applications on |UCSUCS| (UCS). The App Center
uses well-known technologies like `Docker <https://www.docker.com/>`_.

.. _infrastructure:

App Center infrastructure
=========================

The ecosystem consists of the following components:

The App
   is the software plus the collection of metadata like
   configuration, text description, logo, screenshots and more for the
   presentation.

The App Center Repository
   is a central server infrastructure
   managed by Univention that stores the files and data for the app. It
   is the installation source for the app.

The App Center Module on UCS
   is part of the web-based management
   system on UCS. It is the place where UCS administrators install,
   update and uninstall apps in their UCS environment.

The App Catalog
   presents the app portfolio on the `Univention
   website <https://www.univention.com/products/univention-app-center/app-catalog/>`_.

The App Provider Portal
   is the self-service portal for app
   providers where they can create and maintain their app.

The Test App Center
   is the "staging area" for app providers to
   develop and test their apps.

|UCSUCR|
   is the target platform for the app. UCS is technically
   a derivative of Debian GNU/Linux.

For building an app the app developer works with UCS, the app, the App
Provider Portal and the Test App Center.

