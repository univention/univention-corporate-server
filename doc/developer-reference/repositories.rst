.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _chap-repo-add:

************************************
Integration of external repositories
************************************

.. index::
   single: repositories; external

Sometimes it might be necessary to add external repositories, for example when
testing an application which is developed for |UCSUAS|. Such components can be
registered through |UCSUMC| or in |UCSUCR|.

Components can be versioned. This ensures that only components are
installed that are compatible with a UCS version.

empty or unset or ``current``
   The current major-minor version will be used.

   If for example UCS 5.2 is currently in use, only the 5.2 repository will be
   used. Please note that all major and minor updates will be blocked until the
   component is available for the new release. Patch level and errata updates
   are not affected.

   If for example UCS 5.1 is currently installed. When UCS 5.2 or UCS 6.0 become
   available, the release updated will be postponed until the component is also
   available for version 5.2 and 6.0 respectively.

*major.minor*
   By specifying an explicit version number only the specified version of the
   component will be used if it matches the current UCS version. Release updates
   of the system will not be hindered by such components. Multiple versions can
   be given using comma as delimiter.

   For example ``5.1 5.2`` would only include the component with UCS 5.1 and 5.2
   but not if UCS 5.0 or UCS 5.3 is in use.

.. _integration-of-repository-components-through-umc:

Integrate with |UCSUMC|
=======================

A list of the integrated repository components is in the UMC module *Repository
Settings*. Applications which have been added through the Univention App Center
are still listed here, but should be managed through the *App Center* module.

A further component can be set up with :guilabel:`Add`. The *Component name*
identifies the component on the repository server. A free text can be entered
under *Description*, for example, for describing the functions of the component
in more detail.

The absolute URL of the download server is to be entered in the input field
*Repository server*, and can also optionally contain a *Username*, *Password*,
*Repository prefix* (file path) and *port* if required.


.. warning::

   The credentials are stored unencrypted and as plain text in |UCSUCR|.
   Every user with access to the local system can read them.

A software component is only available when *Enable this component* has been
activated.

Prior to UCS 5 two separate repository branches where provided for *maintained*
and *unmaintained* software. While UCS 5 no longer uses this distinction.

.. _computers-softwaremanagement-repo-add-ucr:

Integrate with |UCSUCR|
=======================

You can use the following |UCSUCRVs| to register a repository component.
It's also possible to activate further functions here
that you can't configured through the UMC module.
:samp:`{NAME}` stands for the component's name.

.. envvar:: repository/online/component/NAME/server

   The repository server absolute URL on which the components are available.
   If this variable isn't set,
   UCS uses the server from |UCSUCRV| :envvar:`repository/online/server`.

.. envvar:: repository/online/component/NAME

   You must set this variable to ``enabled``, if UCS should activate and use the component.

.. envvar:: repository/online/component/NAME/localmirror

   You can use this variable to configure whether UCS mirrors the component locally.
   In combination with the |UCSUCRV| :envvar:`repository/online/component/NAME/server`,
   you can set up a configuration so that UCS mirrors the component, but doesn't activate it,
   or that UCS activates the component, but doesn't mirror it.

.. envvar:: repository/online/component/NAME/description

   A optional description for the repository.

.. envvar:: repository/online/component/NAME/prefix

   .. deprecated:: 5.0

   Defines the URL path prefix that the repository server uses.
   Don't use this variable anymore.
   Instead, specify the path as part of the absolute URL in the UCR variable
   :envvar:`repository/online/component/NAME/server`.

   For example: ``repository/online/component/NAME/server=https://repository.example.com/prefix``

.. envvar:: repository/online/component/NAME/layout

   Defines the type of the repository:

   * If the variable has the value ``arch`` or is unset,
     UCS searches for the :file:`Packages` within the architecture subdirectories :file:`amd64/` and :file:`all/` respectively.

   * If the variable has the value ``flat``,
     UCS searches for the :file:`Packages` file within the root directory of the repository.

   This variable is usually unset.

.. envvar:: repository/online/component/NAME/username

   .. deprecated:: 5.0

   The variable defines the username if the repository server requires authentication.
   Don't use this variable anymore.
   Instead, specify the username as part of the absolute URL in the UCR variable
   :envvar:`repository/online/component/NAME/server`.

   For example: ``repository/online/component/NAME/server=https://username@repository.example.com``

.. envvar:: repository/online/component/NAME/password

   .. deprecated:: 5.0

   This variable defines the password if the repository server requires authentication.
   Don't use this variable anymore.
   Instead, specify the password as part of the absolute URL in the UCR variable
   :envvar:`repository/online/component/NAME/server`.

   For example: ``repository/online/component/NAME/server=https://username:password@repository.example.com``

.. envvar:: repository/online/component/NAME/version

   This variable controls the versions to include.
   For more information, see :ref:`chap-repo-add`.

.. envvar:: repository/online/component/NAME/defaultpackages

   Defines a list of package names separated by blanks.
   The UMC module *Repository Settings* offers the installation of this component
   if at least one of the packages isn't installed.
   Specifying the package list eases the subsequent installation of components.
