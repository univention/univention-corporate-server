.. _ucr-usage:

Using UCR
=========

.. highlight:: console

|UCSUCR| provides two interfaces, which allows easy access from shell scripts
and Python programs.

.. _ucr-usage-shell:

Using UCR from shell
--------------------

:command:`univention-config-registry` (and its alias :command:`ucr`) can be
invoked directly from shell. The most commonly used functions are:

:command:`ucr set` :samp:`[ {key}={value} | {key}?{value} ] ...`
   Set |UCSUCRV| ``key`` to the given ``value``. Using ``=`` forces an
   assignment, while ``?`` only sets the value if the variable is unset.

   .. code-block::
      :caption: Use of :command:`ucr set`
      :name: ucr-set

      $ ucr set print/papersize?a4 \
      > variable/name=value


:command:`ucr get` :samp:`{key}`
   Return the current value of the |UCSUCRV| ``key``.

   .. code-block:: bash
      :caption: Use of :command:`ucr get`
      :name: ucr-get

      case "$(ucr get system/role)" in
          domaincontroller_*)
              echo "Running on a UCS Directory Node"
              ;;
      esac


   For variables containing boolean values the shell-library-function
   :samp:`is_ucr_true {key}` from :file:`/usr/share/univention-lib/ucr.sh`
   should be used. It returns ``0`` (success) for the values ``1``, ``yes``,
   ``on``, ``true``, ``enable``, ``enabled``, ``1`` for the negated values
   ``0``, ``no``, ``off``, ``false``, ``disable``, ``disabled``. For all other
   values it returns a value of ``2`` to indicate inappropriate usage.

   .. code-block:: bash
      :caption: Use of ``is_ucr_true``
      :name: ucr-true

      . /usr/share/univention-lib/ucr.sh
      if is_ucr_true update/secure_apt
      then
          echo "The signature check for UCS packages is enabled."
      fi


:command:`ucr unset` :samp:`{key} ...`
   Unset the |UCSUCRV| ``key``.

   .. code-block::
      :caption: Use of :command:`ucr unset`
      :name: ucr-unset

      $ ucr unset print/papersize variable/namme


:command:`ucr shell` :samp:`[ {key} ...]`
   Export some or all |UCSUCRV|\ s in a shell compatible manner as environment
   variables. All shell-incompatible characters in variable names are
   substituted by underscores (``_``).

   .. code-block:: bash
      :caption: Use of command:`ucr shell`
      :name: ucr-shell

      eval "$(ucr shell)"
      case "$server_role" in
          domaincontroller_*)
              echo "Running on a UCS Domain Controller serving $ldap_base"
              ;;
      esac


   It is often easier to export all variables once and than reference the values
   through shell variables.

   .. warning::

      Be careful with shell quoting, since several |UCSUCRV|\ s contain shell
      meta characters. Use :command:`eval "$(ucr shell)"`.

.. note::

   :command:`ucr` is installed as :file:`/usr/sbin/ucr`, which is not on the
   search path :envvar:`$PATH` of normal users. Changing variables requires root
   access to :file:`/etc/univention/base.conf`, but reading works for normal
   users too, if :file:`/usr/sbin/ucr` is invoked directly.

.. _ucr-usage-python:

Using UCR from Python
---------------------

UCR also provides a Python binding, which can be used from any Python program.
An instance of ``univention.config_registry.ConfigRegistry`` needs to be created
first. After loading the current database state with ``load()`` the values can be
accessed by using the instance like a Python dictionary:

.. code-block:: python
   :caption: Reading a Univention Configuration Registry variable in Python
   :name: ucr-python-read

   from univention.config_registry import ConfigRegistry
   ucr = ConfigRegistry()
   ucr.load()
   print(ucr['variable/name'])
   print(ucr.get('variable/name', '<not set>'))


Since UCS 5.0 several new APIs are provided to simplify reading UCR settings:

``ucr``
   This is a lazy-loaded shared instance, which only allows reading values. It
   is implemented as a singleton, so all modules using it share the same
   instance (per process). It can be refreshed by invoking load().

   .. code-block:: python
      :caption: Reading a Univention Configuration Registry variable in Python
      :name: ucr-python-ucr

      from univention.config_registry import ucr
      print(ucr["ldap/base"])


``ucr_live``
   In contrast to ``ucr`` this shared singleton instance automatically reloads
   the settings. This is done on each access, but only happens if the files on
   disk actually changed.

   .. code-block:: python
      :caption: Reading a Univention Configuration Registry variable in Python
      :name: ucr-python-ucr-live

      from univention.config_registry import ucr_live
      print(ucr_live["version/erratalevel"])


   Repeated reads of the same key may return different values due to the live
   character. Reading multiple keys in sequence is not atomic as other processes
   might update UCR in between. Reading many keys is slower due to the extra
   check for updated files. To mitigate this a frozen view (a read-only snapshot
   with auto reload disabled) is created when this instance is used as a Python
   context manager:

   .. code-block:: python
      :caption: Reading a Univention Configuration Registry variable in Python
      :name: ucr-python-ucr-view

      from univention.config_registry import ucr_live
      with ucr_live as view:
          for key, value in view.items():
              print(key, value)


``ucr_factory``
   This function can be used to create a new private instance. All values are
   already loaded.

   .. code-block:: python
      :caption: Reading a Univention Configuration Registry variable in Python
      :name: ucr-python-ucr-factory

      from univention.config_registry import ucr_factory
      ucr = ucr_factory()
      print(ucr["version/erratalevel"])


For variables containing boolean values the methods ``is_true()`` and
``is_false()`` should be used. The former returns ``True`` for the values ``1``,
``yes``, ``on``, ``true``, ``enable``, ``enabled``, while the later one returns
``True`` for the negated values ``0``, ``no``, ``off``, ``false``, ``disable``,
``disabled``. Both methods accept an optional argument ``default``, which is
returned as-is when the variable is not set.

.. code-block:: python
   :caption: Reading boolean Univention Configuration Registry variables in Python
   :name: ucr-python-bool

   if ucr.is_true('update/secure_apt'):
       print("package signature check is explicitly enabled")
   if ucr.is_true('update/secure_apt', True):
       print("package signature check is enabled")
   if ucr.is_false('update/secure_apt'):
       print("package signature check is explicitly disabled")
   if ucr.is_false('update/secure_apt', True):
       print("package signature check is disabled")


Modifying variables requires a different approach. The function ``ucr_update()``
should be used to set and unset variables.

.. code-block:: python
   :caption: Changing Univention Configuration Registry variables in Python
   :name: ucr-python-change

   from univention.config_registry.frontend import ucr_update
   ucr_update(ucr, {
       'foo': 'bar',
       'baz': '42',
       'bar': None,
   })


The function ``ucr_update()`` requires an instance of ``ConfigRegistry``
(returned by ``ucr_factory()``) as its first argument. The method is guaranteed
to be atomic and internally uses file locking to prevent race conditions.

The second argument must be a Python dictionary mapping UCR variable names to
their new value. The value must be either a string or ``None``, which is used to
unset the variable.

As an alternative the old functions ``handler_set()`` and ``handler_unset()``
can still be used to set and unset variables. Both functions expect an array of
strings with the same syntax as used with the command line tool :command:`ucr`.
As the functions ``handler_set()`` and ``handler_unset()`` don't automatically
update any instance of ``ConfigRegistry``, the method load() has to be called
manually afterwards to reflect the updated values.

.. code-block:: python
   :caption: Setting and unsetting Univention Configuration Registry variables in Python
   :name: ucr-python-unset

   from univention.config_registry import handler_set, handler_unset
   handler_set(['foo=bar', 'baz?42'])
   handler_unset(['foo', 'bar'])


.. code-block:: python
   :caption: Getting integer values from Univention Configuration Registry variables in Python
   :name: ucr-python-get-int

   from univention.config_registry import ucr
   print(ucr.get_int("key"))
   print(ucr.get_int("key", 10))
