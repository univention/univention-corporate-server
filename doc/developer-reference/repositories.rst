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

The hostname of the download server is to be entered in the input field
*Repository server*, and, if necessary, an
additional file path in *Repository prefix*.

A *Username* and *Password* can be configured for repository servers which
require authentication.

.. warning::

   The credentials are stored unencrypted and as plain text in |UCSUCR|.
   Every user with access to the local system can read them.

A software component is only available when *Enable this component* has been
activated.

Prior to UCS 5 two separate repository branches where provided for *maintained*
and *unmaintained* software. While UCS 5 no longer uses this distinction, the
mechanism still exists and is used for component repositories.

.. _computers-softwaremanagement-repo-add-ucr:

Integrate with |UCSUCR|
=======================

The following |UCSUCRV|\ s can be used to register a repository component.
It is also possible to activate further functions here which cannot be
configured through the UMC module.
:samp:`{NAME}` stands for the component's name:

:samp:`repository/online/component/{NAME}/server`
   The repository server on which the components are available. If this variable
   is not set, the server from |UCSUCRV| :envvar:`repository/online/server` is
   used.

:samp:`repository/online/component/{NAME}`
   This variable must be set to *enabled* if the components are to be mounted.

:samp:`repository/online/component/{NAME}/localmirror`
   This variable can be used to configure whether the component is mirrored
   locally. In combination with the |UCSUCRV|
   :samp:`repository/online/component/{NAME}/server`, a configuration can be set
   up so that the component is mirrored, but not activated, or that it is
   activated, but not mirrored.

:samp:`repository/online/component/{NAME}/description`
   A optional description for the repository.

:samp:`repository/online/component/{NAME}/prefix`
   Defines the URL prefix which is used on the repository server. This variable
   is usually not set.

:samp:`repository/online/component/{NAME}/layout`
   Defines the type of the repository:

   * If ``arch`` is set or the variable is unset, the :file:`Packages` file is
     searched within the architecture subdirectories :file:`amd64/` resp.
     :file:`all/`.

   * If ``flat`` repository is specified, the :file:`Packages` file is searched
     within the root directory of the repository.

   This variable is usually not set.

:samp:`repository/online/component/{NAME}/username`
   If the repository server requires authentication, the username can be entered
   in this variable.

:samp:`repository/online/component/{NAME}/password`
   If the repository server requires authentication, the password can be entered
   in this variable.

:samp:`repository/online/component/{NAME}/version`
   This variable controls the versions to include, see :ref:`chap-repo-add` for
   details.

:samp:`repository/online/component/{NAME}/defaultpackages`
   A list of package names separated by blanks. The UMC module *Repository
   Settings* offers the installation of this component if at least one of the
   packages is not installed. Specifying the package list eases the subsequent
   installation of components.
