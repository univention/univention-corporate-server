.. _command-univention-app:

Command :command:`univention-app`
=================================

.. program:: univention-app

:command:`univention-app` is a program to manage apps from Univention App Center
on the command line on a UCS system.

This section describes a selection of the available commands. For a complete
list of available commands, run :command:`univention-app` without any arguments
and :samp:`univention-app {<command>} --help` for details on a specific
command.

.. option:: shell [-h] [-u USER] [-i] [-t] [-s SERVICE_NAME] app command

   The :option:`univention-app shell` command allows to run commands within a
   Docker app.

   For multi container apps, :command:`univention-app shell` runs the command in
   the main container which is the default behavior. The app metadata defines
   the app's "main service". For more information about referencing containers,
   see :ref:`create-app-with-docker-compose`.

   To run a command in the main service of the app:

   .. code-block:: console
      :caption: Run a shell command inside the app's main service

      $ univention-app shell <app> <command>

   To run a command in a specific service of the app, such as creating a backup
   of a :program:`MongoDB` database:

   .. code-block:: console
      :caption: Run a shell command inside the app's main service

      $ univention-app shell -s <service-name> <app> mongodump --out /data/backup

   For descriptions of the outline options and arguments of
   :option:`univention-app shell`, refer to the console output of:

   .. code-block:: console
      :caption: Show options and arguments of :option:`univention-app shell`

      $ univention-app shell --help

