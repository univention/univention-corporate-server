.. _umc-module:

Local system module
===================

.. index::
   single: management console; module
   single: management console; system

The UMC server provides management services that are provided by so called UMC
modules. These modules are implemented in Python (back end) and in JavaScript
(web front end). The following page provides information about developing and
packaging of UMC modules. It is important to know the details of
:ref:`umc-architecture`.

The package :program:`univention-management-console-dev` provides the command
:command:`umc-create-module`, which can be used to create a template for a
custom UMC module.

.. _umc-module-python:

Python API
----------

The Python API for the UMCP is defined in the Python module
:py:mod:`univention.management.console.protocol`.

.. _umc-module-api:

UMC module API (Python and JavaScript)
--------------------------------------

A UMC module consists of three components

* A XML document containing the definition.

* The Python module defining the command functions.

* The JavaScript front end providing the web front end.

.. _umc-module-api-xml:

XML definition
~~~~~~~~~~~~~~

The UMC server knows three types of resources that define the functionality it
can provide:

UMC modules
   provide commands that can be executed if the required permission is given.

Syntax types
   can be used to verify the correctness of command attributes defined by the
   UMCP client in the request message or return values provided by the UMC
   modules.

Categories
   help to define a structure and to sort the UMC modules by its type of
   functionality.

All these resources are defined in XML files. The details are described in the
following sections

.. _umc-module-api-xml-definition:

Module definition
"""""""""""""""""

The UMC server does not load the Python modules to get the details about the
modules name, description and functionality. Therefore, each UMC module must
provide an XML file containing this kind of information. The following example
defines a module with the id ``udm``:

.. literalinclude:: udm.xml
   :language: xml

The element ``module`` defines the basic details of a
UMC module.

``id``
   This identifier must be unique among the modules of an UMC server.
   Other files may extend the definition of a module by adding more
   flavors or categories.

``icon``
   The value of this attribute defines an identifier for the icon that
   should be used for the module. Details for installing icons can be
   found in the :ref:`umc-module-packaging`.

``python``
   This value can be used to specify the Python interpreter version, for example
   ``2`` or ``3``. Default is Python 2.

The child elements ``name`` and ``description`` define the English human
readable name and description of the module. For other translations the build
tools will create translation files. Details can be found in the
:ref:`umc-module-packaging`.

This example defines a so called *flavor*. A flavor defines a new name,
description and icon for the same UMC module. This can be used to show several
virtual modules in the overview of the web front end. Additionally, the flavor is
passed to the UMC server with each request i.e. the UMC module has the
possibility to act differently for a specific flavor.

As the next element ``categories`` is defined in the example. The child elements
``category`` set the categories within the overview where the module should be
shown. Each module can be part of multiple categories. The attribute ``name`` is
the internal identifier of a category.

At the end of the definition file a list of commands is specified. The UMC
server only passes commands to a UMC module that are defined. A command
definition has two attributes:

``name``
   is the name of the command that is passed to the UMC module. Within the UMCP
   message it is the first argument after the UMCP ``COMMAND``.

``function``
   defines the method to be invoked within the Python module when the command is
   called.

.. _umc-module-api-xml-category:

Category definition
"""""""""""""""""""

The predefined set of categories can be extended by each module.

.. literalinclude:: categories.xml
   :language: xml
   :caption: UMC module category examples
   :name: umc-module-api-category-example

.. _umc-module-api-python:

Python module
~~~~~~~~~~~~~

The Python API for UMC modules primarily consists of one base class that must be
implemented. As an addition the Python API provides some helpers:

* Exception classes

* Translation support

* Logging functions

* UCR access

In the definition file, the UMC module specifies functions for the commands
provided by the module. These functions must be implemented as methods of the
class :py:class:`Instance` that inherits from
:py:class:`univention.management.console.base.Base`.

The following Python code example matches the definition in the previous
section:

.. literalinclude:: ucr/umc/python/ucr/__init__.py
   :language: python

Each command methods has one parameter that contains the UMCP request. Such an
object has the following properties:

``id``
   the unique identifier of the request.

``options``
   contains the arguments for the command. For most commands it is a dictionary.

``flavor``
   the name of the flavor that was used to invoke the command. This might be
   ``None``.

The method ``init()`` in the example is invoked when the module process starts.
It could for example be used to initialize a database connection.

The other methods in the example will serve specific requests. To respond to a
request the function ``finished()`` must be invoked. To validate the request
body the decorator ``@sanitize`` might be used with various sanitizers defined
in :py:class:`univention.management.console.modules.sanitizers`.

For a way to send an error message back to the client the :py:class:`UMC_Error`
can be raised with the error message as argument and an optional HTTP status
code. The base class for modules provides some properties and methods that could
be useful when writing UMC modules:

``username``
   The username of the owner of this session.

``user_dn``
   The DN of the user or None if the user is only a local user.

``password``
   The password of the user.

``init()``
   Is invoked after the module process has been initialized. At that moment, the
   settings, like locale and username and password are available.

``destroy()``
   Is invoked before the module process shuts down.

.. _umc-module-api-storepython:

UMC store API
~~~~~~~~~~~~~

In order to encapsulate and ease the access to module data from the JavaScript
side, a store object offers a unified way to query and modify module data.

The UMC JavaScript API comes with an object store implementation of the `Dojo
store API <dojo-store_>`_. This allows the JavaScript code to access/modify
module data and to observe changes on the data in order to react immediately.
The following methods are supported:

.. js:function:: get(id)

   Returns a dictionary of all properties for the object with the
   specified identifier.

.. js:function:: put(dictionary, options)

   modifies an object with the corresponding properties and an optional
   dictionary of options.

.. js:function:: add(dictionary, options)

   Adds a new object with the corresponding properties and an optional
   dictionary of options.

.. js:function:: remove(id)

   Removes the object with the specified identifier.

.. js:function:: query(dictionary)

   Queries a list of objects (returned as list of dictionaries) corresponding to
   the given query which is represented as dictionary. Note that not all object
   properties need to be returned in order to save bandwidth.

The UMC object store class in JavaScript will be able to communicate directly
with the Python module if the following methods are implemented:

.. js:function:: module/get

   Expects as input a list if unique IDs (as strings) and returns a list of
   dictionaries as result. Each dictionary entry holds all object properties.

.. js:function:: module/put

   Expects as input a list of dictionaries where each entry has the properties
   ``object`` and ``options``. The property ``object`` holds all object
   properties to be set (i.e., this may also be a subset of all possible
   properties) as a dictionary. The second property ``options`` is an optional
   dictionary that holds additional options as a dictionary.

.. js:function:: module/add

   Expects similar input values as :js:func:`module/put`.

.. js:function:: module/remove

   Expects as input a list of dictionaries where each entry has the properties
   ``object`` (containing the object's unique ID (as string)) and ``options``.
   The options property can be necessary as a removal might be executed in
   different ways (recursively, shallow removal etc.).

.. js:function:: module/query

   Expects as input a dictionary with entries that specify the query parameters
   and returns a list of dictionaries. Each entry may hold only a subset of all
   possible object properties.

Further references:

* `Dojo object store reference guide <dojo-store_>`_

* `Object store tutorial <dojo-object-store_>`_

* `HTML5 IndexedDB object store API <w3-object-store_>`_

.. _umc-module-packaging:

Packaging
---------

A UMC module consists of several files that must be installed at a specific
location. As this mechanism is always the same there are :program:`debhelper`
tools making package creation for UMC modules very easy.

The following example is based on the package for the UMC module UCR.

A UMC module may be part of a source package with multiple binary packages. The
examples uses a own source package for the module.

As a first step create a source package with the following directories and
files:

* :file:`univention-management-console-module-ucr/`

* :file:`univention-management-console-module-ucr/debian/`

* :file:`univention-management-console-module-ucr/debian/univention-management-console-module-ucr.umc-modules`

* :file:`univention-management-console-module-ucr/debian/rules`

* :file:`univention-management-console-module-ucr/debian/changelog`

* :file:`univention-management-console-module-ucr/debian/control`

* :file:`univention-management-console-module-ucr/debian/copyright`

All these files are standard Debian packaging files except
:file:`univention-management-console-module-ucr.umc-modules`. This file contains
information about the locations of the UMC module source files:

.. literalinclude:: ucr/debian/univention-management-console-module-ucr.umc-modules


The keys in this file of the following meaning:

``Module``
   The internal name of the module

``Python``
   A directory that contains the Python package for the UMC module

``Definition``
   The filename of the XML file with the module definition

``Javascript``
   A directory containing the JavaScript source code

``Icons``
   A directory containing the icons required by the modules web front end

``Syntax`` (optional)
   The filename of the XML file with the syntax definitions

``Category`` (optional)
   The filename of the XML file with the category definitions

The directory structure for such a UMC module file would look like this:

* :file:`univention-management-console-module-ucr/umc/`

* :file:`univention-management-console-module-ucr/umc/syntax/`

* :file:`univention-management-console-module-ucr/umc/syntax/ucr.xml`

* :file:`univention-management-console-module-ucr/umc/js/`

* :file:`univention-management-console-module-ucr/umc/js/ucr.js`

* :file:`univention-management-console-module-ucr/umc/js/de.po`

* :file:`univention-management-console-module-ucr/umc/de.po`

* :file:`univention-management-console-module-ucr/umc/icons/`

* :file:`univention-management-console-module-ucr/umc/icons/16x16/`

* :file:`univention-management-console-module-ucr/umc/icons/16x16/ucr.png`

* :file:`univention-management-console-module-ucr/umc/icons/24x24/`

* :file:`univention-management-console-module-ucr/umc/icons/24x24/ucr.png`

* :file:`univention-management-console-module-ucr/umc/icons/64x64/`

* :file:`univention-management-console-module-ucr/umc/icons/64x64/ucr.png`

* :file:`univention-management-console-module-ucr/umc/icons/32x32/`

* :file:`univention-management-console-module-ucr/umc/icons/32x32/ucr.png`

* :file:`univention-management-console-module-ucr/umc/ucr.xml`

* :file:`univention-management-console-module-ucr/umc/python/`

* :file:`univention-management-console-module-ucr/umc/python/ucr/`

* :file:`univention-management-console-module-ucr/umc/python/ucr/de.po`

* :file:`univention-management-console-module-ucr/umc/python/ucr/__init__.py`

If such a package has been created a few things need to be adjusted

:file:`debian/rules`
   .. literalinclude:: ucr/debian/rules
      :language: make

:file:`debian/control`
   .. literalinclude:: ucr/debian/control
      :language: control
