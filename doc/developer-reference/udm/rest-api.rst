.. SPDX-FileCopyrightText: 2021-2025 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _udm-rest-api:

|UCSREST|
=========

.. _udm-rest-api-authentication:
.. _udm-rest-api-overview:
.. _udm-rest-api-usage-examples:
.. _udm-rest-api-usage-examples-post:
.. _udm-rest-api-usage-examples-get:
.. _udm-rest-api-usage-examples-put:
.. _udm-rest-api-usage-examples-delete:
.. _udm-rest-api-error-codes:

The content about the *UDM HTTP REST API* moved to another document.
Except for the section about :ref:`udm-rest-api-clients`,
continue reading at
:external+uv-nubus-kubernetes-customization:ref:`customization-api-udm-rest`
in :cite:t:`uv-nubus-kubernetes-customization`.

.. seealso::

   For an architectural overview,
   see :external+uv-architecture:ref:`services-udm-rest-api`
   in :cite:t:`ucs-architecture`.

.. _udm-rest-api-clients:

API clients
-----------

The following API clients implemented in Python exist for the |UCSREST|:

* :program:`python3-univention-directory-mananger-rest-client`:

  Every UCS system has it installed by default.
  You can use it the following way:

  .. code-block:: python
     :caption: Example for using Python |UCSREST| client

     from univention.admin.rest.client import UDM

     uri = 'https://ucs-primary.example.com/univention/udm/'
     udm = UDM.http(uri, 'Administrator', 'univention')
     module = udm.get('users/user')

     # 1. create a user
     obj = module.new()
     obj.properties['username'] = 'foo'
     obj.properties['password'] = 'univention'
     obj.properties['lastname'] = 'foo'
     obj.save()

     # 2. search for users (first user)
     obj = next(module.search('uid=*'))
     if obj:
         obj = obj.open()
     print('Object {}'.format(obj))

     # 3. get by dn
     ldap_base = udm.get_ldap_base()
     obj = module.get('uid=foo,cn=users,%s' % (ldap_base,))

     # 4. get referenced objects e.g. groups
     pg = obj.objects['primaryGroup'].open()
     print(pg.dn, pg.properties)
     print(obj.objects['groups'])

     # 5. modify
     obj.properties['description'] = 'foo'
     obj.save()

     # 6. move to the ldap base
     obj.move(ldap_base)

     # 7. remove
     obj.delete()

* :program:`python3-univention-directory-mananger-rest-async-client`:

  After installing the Debian package on a UCS system,
  you can use it in the following way:

  .. code-block:: python
     :caption: Example for using Python asynchronous UDM REST API client

     import asyncio
     from univention.admin.rest.async_client import UDM

     uri = 'https://ucs-primary.example.com/univention/udm/'

     async def main():
         async with UDM.http(uri, 'Administrator', 'univention') as udm:
             module = await udm.get('users/user')

             # 1. create a user
             obj = await module.new()
             obj.properties['username'] = 'foo'
             obj.properties['password'] = 'univention'
             obj.properties['lastname'] = 'foo'
             await obj.save()

             # 2. search for users (first user)
             objs = module.search()
             async for obj in objs:
                 if not obj:
                     continue
                 obj = await obj.open()
                 print('Object {}'.format(obj))

             # 3. get by dn
             ldap_base = await udm.get_ldap_base()
             obj = await module.get('uid=foo,cn=users,%s' % (ldap_base,))

             # 4. get referenced objects e.g. groups
             pg = await obj.objects['primaryGroup'].open()
             print(pg.dn, pg.properties)
             print(obj.objects['groups'])

             # 5. modify
             obj.properties['description'] = 'foo'
             await obj.save()

             # 6. move to the ldap base
             await obj.move(ldap_base)

             # 7. remove
             await obj.delete()

* Python |UCSREST| Client:

  * `Package at PyPI <https://pypi.org/project/udm-rest-api-client/>`_
  * :external+python-udm-rest-client:doc:`Documentation <index>`

.. spelling:word-list::

   Unprocessable
