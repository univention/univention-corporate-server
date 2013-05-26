.. Univention Documentation documentation master file, created by sphinx-quickstart on Tue Jun 12 14:02:29 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Univention Doc
========================

Univention Doc is a tool to create source documentation based on
sphinx. It builds the documentations and creates an index web page
listing all available documentations. This documentation itself is
created using Univention Doc :-)

To add a source documentation you first need to understand the basics of
Sphinx and reStructuredText. Information can be found on the following
websites:

* `Sphinx documentation <http://sphinx.pocoo.org/contents.html>`_
* `reStructuredText Primer <http://sphinx.pocoo.org/rest.html>`_
* `reStructuredText user documentation <http://docutils.sourceforge.net/rst.html>`_

==========================
Creating the documentation
==========================

At first you should create a subdirectory within your source package
like *doc*. In this directory the documentation and configuration files
will be located. To start with the documentation the package
*python-sphinx* must be installed ::

 univention-install python-sphinx

If the package is installed call the quickstart tool of sphinx ::

 cd doc
 sphinx-quickstart

The tool will create a basic configuration for the documentation based
on a few questions that you have to answer. You should let the tool
create a Makefile as it helps building the documentation during
development.

Alternatively you may copy the configuration file *conf.py*, the
Makefile and the index.rst from the UMC source package

`Web SVN access to UMC <https://forge.univention.org/websvn/listing.php?repname=dev&path=%2Fbranches%2Fucs-3.0%2Fucs%2Fmanagement%2Funivention-management-console%2F&#a163ea89c19c4eaaad2950435ff70dc08>`_

When you have copied the files you should at least replace all
occurrences of *Univention Management Console*. After that you can start
writing your documentation.

=========
Packaging
=========

To package the documentation just a few steps are necessary:

1. Add a new binary package to your source package, like ::

     Package: <package name>-doc
     Architecture: all
     Depends: ${misc:Depends},
      univention-doc
     Description: <package description> - documentation

   Replace *<package name>* and *<package description>* with some useful texts.

2. Create an *debian/<package name>-doc.install* file for the binary package containing at least the following entries ::

     doc/*.rst usr/share/univention-doc/src/<package name>/
     doc/*.png usr/share/univention-doc/src/<package name>/
     doc/*.py usr/share/univention-doc/src/<package name>/

   Replace *<package name>* with the name of your package.

3. Create a *debian/<package name>.postinst* file for the binary package and add at least the following line ::

     univention-doc install <package name>

4. Create a *debian/<package name>.prerm* file for the binary package and add at least the following line ::

     univention-doc uninstall <package name>


