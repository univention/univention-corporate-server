.. _ucr-build:

Build integration
=================

During package build time :command:`univention-install-config-registry` needs to
be called. This should be done using the sequence ``ucr`` in
:file:`debian/rules`:

.. code-block:: makefile

   %:
       dh $@ --with ucr

This invocation copies the referenced files to the right location in the binary
package staging area :samp:`debian/{package}/etc/univention/`. Internally
:command:`univention-install-config-registry-info` and
:command:`univention-install-service-info` are invoked, which should not be
called explicitly anymore.

The calls also insert code into the files
:file:`debian/{package}.preinst.debhelper`,
:file:`debian/{package}.postinst.debhelper` and
:file:`debian/{package}.prerm.debhelper` to register and de-register the
templates. Therefore it's important that customized maintainer scripts use the
``#DEBHELPER#`` marker, so that the generated code gets inserted into the
corresponding :file:`preinst`, :file:`postinst` and :file:`prerm` files of the
generated binary package.

The invocation also adds :program:`univention-config` to ``misc:Depends`` to
ensure that the package is available during package configuration time.
Therefore it's important that ``${misc:Depends}`` is used in the ``Depends``
line of the package section in the :file:`debian/control` file.

.. code-block::

   Package: ...
   Depends: ..., ${misc:Depends}, ...
