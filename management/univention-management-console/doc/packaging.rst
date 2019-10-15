.. _chapter-packaging:

---------
Packaging
---------

A UMC module consists of several files that must be installed at a
specific location. As this mechanism is always the same there are
debhelper tools making package creation for UMC modules very easy.

The following example is based on the package for the UMC module UCR.

A UMC module may be part of a source package with multiple binary
packages. The examples uses a distinct source package for the module.

As a first step create a source package with the following files: ::

		univention-management-console-module-ucr
		univention-management-console-module-ucr/debian
		univention-management-console-module-ucr/debian/univention-management-console-module-ucr.umc-modules
		univention-management-console-module-ucr/debian/rules
		univention-management-console-module-ucr/debian/changelog
		univention-management-console-module-ucr/debian/control
		univention-management-console-module-ucr/debian/copyright
		univention-management-console-module-ucr/debian/compat

All these files are standard debian packaging files except
*univention-management-console-module-ucr.umc-modules*. This file
contains information about the locations of the UMC module source files: ::

		Module: ucr
		Python: umc/python
		Definition: umc/ucr.xml
		Javascript: umc/js
		Icons: umc/icons

The meaning of the keys in this file are described in the following:

Module
	The internal name of the module
Python
	A directory that contains the python package for the UMC module
Definition
	The filename of the XML file with the module definition
Javascript
	A directory containing the javascript source code
Icons
	A directory containing the icons required by the modules web frontend
Category (optional)
	The filename of the XML file with the category definitions

The directory structure a UMC module complying with this example file
would look like this: ::

		univention-management-console-module-ucr/umc
		univention-management-console-module-ucr/umc/js
		univention-management-console-module-ucr/umc/js/ucr.js
		univention-management-console-module-ucr/umc/js/de.po
		univention-management-console-module-ucr/umc/de.po
		univention-management-console-module-ucr/umc/icons
		univention-management-console-module-ucr/umc/icons/16x16
		univention-management-console-module-ucr/umc/icons/16x16/ucr.png
		univention-management-console-module-ucr/umc/icons/24x24
		univention-management-console-module-ucr/umc/icons/24x24/ucr.png
		univention-management-console-module-ucr/umc/icons/64x64
		univention-management-console-module-ucr/umc/icons/64x64/ucr.png
		univention-management-console-module-ucr/umc/icons/32x32
		univention-management-console-module-ucr/umc/icons/32x32/ucr.png
		univention-management-console-module-ucr/umc/ucr.xml
		univention-management-console-module-ucr/umc/python
		univention-management-console-module-ucr/umc/python/ucr
		univention-management-console-module-ucr/umc/python/ucr/de.po
		univention-management-console-module-ucr/umc/python/ucr/__init__.py

If such a package has been created a few things need to be adjusted

* debian/compat ::

	7

* debian/rules ::

	%:
    	dh $@

	override_dh_auto_build:
		dh-umc-module-build
		dh_auto_build

	override_dh_auto_install:
		dh-umc-module-install
		dh_auto_install

* debian/control ::

		Source: univention-management-console-module-ucr
		Section: univention
		Priority: optional
		Maintainer: Univention GmbH <packages@univention.de>
		Build-Depends: debhelper (>= 7.0.50~),
		 dh-python,
		 univention-management-console-dev,
		 python-all
		 python3-all
		Standards-Version: 3.5.2
		XS-Python-Version: all
		 
		Package: univention-management-console-module-ucr
		Architecture: all
		Depends:
		 univention-management-console-server,
		 ${python:Depends},
		 ${python3:Depends},
		Description: UMC module for UCR
		 This package contains the UMC module for Univention Configuration Registry
