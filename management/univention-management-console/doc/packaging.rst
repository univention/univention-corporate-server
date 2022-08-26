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

		univention-management-console-module-ucr/
			debian/
				changelog
				compat
				control
				copyright
				rules
				source/
					format
				univention-management-console-module-ucr.umc-modules

All these files are standard debian packaging files except
*univention-management-console-module-ucr.umc-modules*. This file
contains information about the locations of the UMC module source files:

.. code-block:: ini

	Module: ucr
	Python: umc/python
	Definition: umc/ucr.xml
	Javascript: umc/js
	Icons: umc/icons

The meaning of the keys in this file are described in the following:

Module
	The internal name of the module
Python
	A directory that contains the Python package for the UMC module
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

		univention-management-console-module-ucr/
			umc/
				js/
					ucr.js
					de.po
				de.po
				icons/
					16x16/
						ucr.png
					24x24/
						ucr.png
					32x32/
						ucr.png
					64x64/
						ucr.png
				ucr.xml
				python/
					ucr/
						de.po
						__init__.py

If such a package has been created a few things need to be adjusted

* debian/compat ::

	9

* debian/rules

	.. code-block:: make

		%:
			dh $@ --with umc

* debian/control

	.. code-block:: debcontrol

		Source: univention-management-console-module-ucr
		Section: univention
		Priority: optional
		Maintainer: Univention GmbH <packages@univention.de>
		Build-Depends:
		  debhelper,
		  dh-python,
		  python3-all,
		  univention-management-console-dev (>= 12.0.2),
		Standards-Version: 3.5.2
		XS-Python-Version: all

		Package: univention-management-console-module-ucr
		Architecture: all
		Depends:
		  univention-management-console-server,
		  ${python3:Depends},
		Provides: ${python3:Provides}
		Description: UMC module for UCR
		  This package contains the UMC module for Univention Configuration Registry
