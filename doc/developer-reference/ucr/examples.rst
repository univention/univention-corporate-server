.. _ucr-example:

Examples
========

.. index::
   pair: config registry; examples

.. SG: Move this to a sample package

This sections contains several simple examples for the use of |UCSUCR|. The
complete source of these examples is available separately. The download location
is given in each example below. Since almost all |UCSUCS| packages use UCR,
their source code provides additional examples.

.. _ucr-example-minimal:

Minimal File example
--------------------

.. index::
   pair: config registry; examples
   pair: examples; single file

This example provides a template for :file:`/etc/papersize`, which is used to
configure the default paper size. A |UCSUCRV| :envvar:`print/papersize` is
registered, which can be used to configure the paper size.

Source code: :uv:src:`doc/developer-reference/ucr/papersize/`

:file:`conffiles/etc/papersize`
   The template file only contains one line. Please note that this file does not
   start with the “UCRWARNING”, since the file must only contain the paper size
   and no comments.

   .. code-block::

      @%@print/papersize@%@

:file:`debian/papersize.univention-config-registry`
   The file defines the templates and is processed by
   :command:`univention-install-config-registry` during the package build and
   afterwards by :command:`univention-config-registry` during normal usage.

   .. code-block::

      Type: file
      File: etc/papersize

:file:`debian/papersize.univention-config-registry-variables`
   The file describes the newly defined |UCSUCRV|.

   .. code-block:: ini

      [print/papersize]
      Description[en]=specify preferred paper size [a4]
      Description[de]=Legt die bevorzugte Papiergröße fest [a4]
      Type=str
      Categories=service-cups

:file:`debian/papersize.postinst`
   Sets the |UCSUCRV| to a default value after package installation.

   .. code-block:: bash

      #!/bin/sh

      case "$1" in
      configure)
      	ucr set print/papersize?a4
      	;;
      esac

      #DEBHELPER#

      exit 0

:file:`debian/rules`
   Invoke :command:`univention-install-config-registry` during package build to
   install the files to the appropriate location. It also creates the required
   commands for the maintainer scripts (see :ref:`deb-scripts`) to register and
   unregister the templates during package installation and removal.

   .. code-block:: makefile

      #!/usr/bin/make -f
      %:
      	dh $@ --with ucr

   .. note::

      Tabulators must be used for indentation in this :program:`Makefile`-type
      file.

:file:`debian/control`
   The automatically generated dependency on :program:`univention-config` is
   inserted by :command:`univention-install-config-registry` through
   :file:`debian/papersize.substvars`.

   .. code-block::

      Source: papersize
      Section: univention
      Priority: optional
      Maintainer: Univention GmbH <packages@univention.de>
      Build-Depends:
       debhelper-compat (= 12),
       univention-config-dev (>= 15.0.3),
      Standards-Version: 4.3.0.3

      Package: papersize
      Architecture: all
      Depends: ${misc:Depends}
      Description: An example package to configure the papersize
       This purpose of this package is to show how Univention Config
       Registry is used.
       .
       For more information about UCS, refer to:
       https://www.univention.de/

.. _ucr-example-multifile:

Multifile example
--------------------------------------------------

.. index::
   pair: config registry; examples
   pair: examples; multi file

This example provides templates for :file:`/etc/hosts.allow` and
:file:`/etc/hosts.deny`, which is used to control access to system services. See
hosts_access5 for more details.

Source code: :uv:src:`doc/developer-reference/ucr/hosts/`

:file:`conffiles/etc/hosts.allow.d/00header`; :file:`conffiles/etc/hosts.deny.d/00header`
   The first file fragment of the file. It starts with ``@%@UCRWARNING=# @%@``,
   which is replaced by the warning text and a list of all subfiles.

   .. code-block::

      @%@UCRWARNING=# @%@
      # /etc/hosts.allow: list of hosts that are allowed to access the system.
      #                   See the manual pages hosts_access(5) and hosts_options(5).

:file:`conffiles/etc/hosts.allow.d/50dynamic``; :file:`conffiles/etc/hosts.deny.d/50dynamic`
   A second file fragment, which uses Python code to insert access control
   entries configured through the |UCSUCRV|\ s ``hosts/allow/`` and
   ``hosts/deny/``.

   .. code-block::

      @!@
      for key, value in sorted(configRegistry.items()):
          if key.startswith('hosts/allow/'):
          print(value)
      @!@


:file:`debian/hosts.univention-config-registry`
   The file defines the templates and is processed by
   :command:`univention-install-config-registry`.

   .. code-block::

      Type: multifile
      Multifile: etc/hosts.allow

      Type: subfile
      Multifile: etc/hosts.allow
      Subfile: etc/hosts.allow.d/00header

      Type: subfile
      Multifile: etc/hosts.allow
      Subfile: etc/hosts.allow.d/50dynamic
      Variables: ^hosts/allow/.*

      Type: multifile
      Multifile: etc/hosts.deny

      Type: subfile
      Multifile: etc/hosts.deny
      Subfile: etc/hosts.deny.d/00header

      Type: subfile
      Multifile: etc/hosts.deny
      Subfile: etc/hosts.deny.d/50dynamic
      Variables: ^hosts/deny/.*

:file:`debian/hosts.univention-config-registry-variables`
   The file describes the newly defined |UCSUCRV|\ s.

   .. code-block:: ini

      [hosts/allow/.*]
      Description[en]=An permissive access control entry for system services, e.g. "ALL: LOCAL"
      Description[de]=Eine erlaubende Zugriffsregel für Systemdienste, z.B. "ALL: LOCAL".
      Type=str
      Categories=service-net

      [hosts/deny/.*]
      Description[en]=An denying access control entry for system services, e.g. "ALL: ALL".
      Description[de]=Eine verbietende Zugriffsregel für Systemdienste, z.B. "ALL: ALL".
      Type=str
      Categories=service-net

.. _ucr-example-service:

Services
----------------------------------------

.. index::
   pair: config registry; examples
   pair: examples; services

.. SG: This is not directly UCR

.. PMH: It shows how an existing init-script is modified to use the
   autostart-UCRV. univention-install-service-info is also automatically
   invoked through univention-install-config-registry. The logic is in
   univention-config, UMC only adds the graphical UI.

This example provides a template to control the :command:`atd` service through
an |UCSUCRV| :envvar:`atd/autostart`.

Source code: :uv:src:`doc/developer-reference/ucr/service/`

:file:`conffiles/etc/init.d/atd`
   The template replaces the original file with a version, which checks the
   |UCSUCRV| :envvar:`atd/autostart` before starting the :command:`at` daemon.
   Please note that the “UCRWARNING” is put after the hash-bash line.

   .. code-block:: bash

      #! /bin/sh
      @%@UCRWARNING=# @%@
      ### BEGIN INIT INFO
      # Provides:          atd
      # Required-Start:    $syslog $time $remote_fs
      # Required-Stop:     $syslog $time $remote_fs
      # Default-Start:     2 3 4 5
      # Default-Stop:      0 1 6
      # Short-Description: Deferred execution scheduler
      # Description:       Debian init script for the atd deferred executions
      #                    scheduler
      ### END INIT INFO
      # pidfile: /var/run/atd.pid
      #
      # Author:	Ryan Murray <rmurray@debian.org>
      #

      PATH=/bin:/usr/bin:/sbin:/usr/sbin
      DAEMON=/usr/sbin/atd
      PIDFILE=/var/run/atd.pid

      test -x "$DAEMON" || exit 0

      . /lib/lsb/init-functions

      case "$1" in
        start)
      	log_daemon_msg "Starting deferred execution scheduler" "atd"
      	start_daemon -p "$PIDFILE" "$DAEMON"
      	log_end_msg $?
          ;;
        stop)
      	log_daemon_msg "Stopping deferred execution scheduler" "atd"
      	killproc -p "$PIDFILE" "$DAEMON"
      	log_end_msg $?
          ;;
        force-reload|restart)
          "$0" stop
          "$0" start
          ;;
        status)
          status_of_proc -p "$PIDFILE" "$DAEMON" atd && exit 0 || exit $?
          ;;
        *)
          echo "Usage: $0 {start|stop|restart|force-reload|status}"
          exit 1
          ;;
      esac

      exit 0

   .. note::

      The inclusion of :file:`init-autostart.lib` and use of
      :command:`check_autostart`.

:file:`debian/service.univention-config-registry`
   The file defines the templates.

   .. code-block::

      Type: file
      File: etc/init.d/atd
      Mode: 755
      Variables: atd/autostart

   .. note::

      The additional ``Mode`` statement to mark the file as executable.

:file:`debian/service.univention-config-registry-variables`
   The file adds a description for the |UCSUCRV|
   :envvar:`atd/autostart`.

   .. code-block:: ini

      [atd/autostart]
      Description[en]=Automatically start the AT daemon on system startup [yes]
      Description[de]=Automatischer Start des AT-Dienstes beim Systemstart [yes]
      Type=bool
      Categories=service-at

:file:`debian/service.postinst`
   Set the |UCSUCRV| to automatically start the :command:`atd`
   on new installations.

   .. code-block:: bash

      #!/bin/sh

      case "$1" in
      configure)
      	ucr set atd/autostart?yes
      	;;
      esac

      #DEBHELPER#

      exit 0

:file:`debian/control`
   :program:`univention-base-files` must be added manually as
   an additional dependency, since it is used from within the shell
   code.

   .. code-block::

      Source: service
      Section: univention
      Priority: optional
      Maintainer: Univention GmbH <packages@univention.de>
      Build-Depends:
       debhelper-compat (= 12),
       univention-config-dev (>= 15.0.3),
      Standards-Version: 4.3.0.3

      Package: service
      Architecture: all
      Depends: ${misc:Depends},
       univention-base-files,
      Description: An example package to configure services
       This purpose of this package is to show how Univention Config
       Registry is used.
       .
       For more information about UCS, refer to:
       https://www.univention.de/
