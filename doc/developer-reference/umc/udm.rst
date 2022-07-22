.. _umc-udm:

Domain LDAP module
==================

.. index::
   single: management console; Module
   single: management console; LDAP

Done through flavor.

.. literalinclude:: module-udm.xml
   :language: xml

Must use ``/umc/module/category/@name="domain"``!

Must use ``/umc/module/@translationId`` to specify alternative translation file,
which must be installed as
:file:`/usr/share/univention-management-console/i18n/{language}/{module}.mo`.
