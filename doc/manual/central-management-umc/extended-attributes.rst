.. _central-extended-attrs:

Expansion of UMC modules with extended attributes
=================================================

The domain management UMC modules allow the comprehensive management of the data
in a domain. *Extended attributes* offer the possibility of integrating new
attributes in the domain management which are not covered by the UCS standard
scope. Extended attributes are also employed by third party vendors for the
integration of solutions in UCS.

Extended attributes are managed in the UMC module :guilabel:`LDAP directory`.
There one needs to switch to the ``univention`` container and then to the
``custom attributes`` subcontainer. Existing attributes can be edited here or a
new :guilabel:`Settings: extended attribute` object created here with
:guilabel:`Add`.

.. _umc-extended-attrs-figure:

.. figure:: /images/umc_extended_attribute.*
   :alt: Extended attribute for managing a car license

Extended attributes can be internationalized. In this case, the name and
description should be compiled in English as this is the standard language for
UMC modules.

.. _central-extended-attrs-general-tab:

Extended attributes - General tab
---------------------------------

.. _central-extended-attrs-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Unique name
     - The name of the LDAP object which will be used to store the extended
       attribute. Within a container, the name has to be unique.

   * - UDM CLI name
     - The specified attribute name should be used when employing the command
       line interface |UCSUDM|. When the extended attribute is saved, the
       *Unique name* of the *General* tab is automatically adopted and can be
       subsequently modified.

   * - Short description
     - Used as title of the input field in UMC modules or as the attribute
       description in the command line interface.

   * - Translations of short description
     - Translated short descriptions can be saved in several languages so that
       the title of extended attributes is also output with other language
       settings in the respective national language. This can be done by
       assigning the respective short description to a language code (e.g.,
       ``de_DE`` or ``fr_FR``) in this input field.

   * - Long description
     - This long description is shown as a tool tip in the input fields in UMC
       modules.

   * - Translations of long description
     - Additional information displayed in the tool tip for an extended
       attribute can also be saved for several languages. This can be done by
       assigning the respective long description to a language code (e.g.,
       ``de_DE`` or ``fr_FR``) in this input field.

.. _central-extended-attrs-module-tab:

Extended attributes - Module tab
--------------------------------

.. _central-extended-attrs-module-tab-table:

.. list-table:: *Module* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Modules to be extended
     - The |UCSUDM| module which is to be expanded with the extended attribute.
       An extended attribute can apply for multiple modules.
   * - Required options/object classes
     - Some extended attributes can only be used practically if certain object
       classes are activated on the :guilabel:`Options` tab. One or more options
       can optionally be saved in this input field so that this extended
       attribute is displayed or editable.
   * - Hook class
     - The functions of the hook class specified here are used during saving,
       modifying and deleting the objects with extended attributes. Additional
       information can be found in :cite:t:`developer-reference`.

.. _central-extended-attrs-ldap-mapping-tab:

Extended attributes - LDAP mapping tab
--------------------------------------

.. _central-extended-attrs-ldap-mapping-tab-table:

.. list-table:: *LDAP mapping* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - LDAP object class
     - Object class to which the attribute entered under *LDAP
       attribute* belongs.

       Predefined LDAP schema extensions for extended attributes are provided
       with the object class ``univentionFreeAttributes``. Further information
       can be found in :ref:`domain-ldap-extensions`.

       Each LDAP object which should be extended with an attribute is
       automatically extended with the LDAP object class specified here if a
       value for the extended attribute has been entered by the user.

   * - LDAP attribute
     - The name of the LDAP attribute where the values of the LDAP object are to
       be stored. The LDAP attribute must be included in the specified object
       class.

   * - Remove object class if the attribute is removed
     - If the value of an extended attribute in a UMC module is deleted, the
       attribute is removed from the LDAP object. If no further attributes of
       the registered object class are used in this LDAP object, the *LDAP
       object class* will also be removed from the LDAP object if this option is
       activated.

.. _central-extended-attrs-umc-tab:

Extended attributes - UMC tab
-----------------------------

.. _central-extended-attrs-umc-tab-table:

.. list-table:: *UMC* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Do not show this extended attribute in UMC modules
     - This option can be activated if an attribute should only be administrated
       internally instead of by the administrator, e.g., indirectly by scripts.
       The attribute can then only be set via the command line interface
       |UCSUDM| and is not displayed in UMC modules.

   * - Exclude from UMC module
     - If it should not be possible to search for an extended attribute in the
       search window of a wizard, this option can be activated to remove the
       extended attribute from the list of possible search criteria.

       This is only needed in exceptional cases.

   * - Ordering number
     - If several extended attributes are to be managed on one tab, the order of
       the individual attributes on the tab can be influenced here. They are
       added to the end of the tab or the group in question in ascending order
       of their numbers.

       Assigning consecutive position numbers results in the attributes being
       ordered on the left and right alternately in two columns. Otherwise, the
       positioning starts in the left column. If additional attributes have the
       same position number, their order is random.

   * - Overwrite existing widget
     - In some cases it is useful to overwrite predefined input fields with
       extended attributes. If the internal UDM name of an attribute is
       configured here, its input field is overwritten by this extended
       attribute. The UDM attribute name can be identified with the command
       :command:`univention-directory-manager` (see :ref:`central-udm`). This
       option may cause problems if it is applied to a mandatory attribute.

   * - Span both columns
     - As standard all input fields are grouped into two columns. This option
       can be used for overlong input fields, which need the full width of the
       tab.

   * - Tab name
     - The name of the tab in UMC modules on which the extended attribute should
       be displayed. New tabs can also be added here.

       If no tab name is entered, *user-defined* will be used.

   * - Translations of tab name
     - Translated tab names can be assigned to the corresponding language code
       (e.g. ``de_DE`` or ``fr_FR``) in this input field.

   * - Overwrite existing tab
     - If this option is activated, the tab in question is overwritten before
       the extended attributes are positioned on it. This option can be used to
       hide existing input fields on a predefined tab. It must be noted that
       this option can cause problems with compulsory fields. If the tab to be
       overwritten uses translations, the overwriting tab must also include
       identical translations.

   * - Tab with advanced settings
     - Settings possibilities which are rarely used can be placed in the
       extended settings tab

   * - Group name
     - Groups allow the structuring of a tab. A group is separated by a gray
       horizontal bar and can be shown and hidden.

       If no group name is specified for an extended attribute, the attribute is
       placed above the first group entry.

   * - Translations of group name
     - To translate the name of the group, translated group names for the
       corresponding language code can be saved in this input field (e.g.,
       ``de_DE`` or ``fr_FR``).

   * - Group ordering number
     - If multiple groups are managed in one tab, this position number can be
       used to specify the order of the groups. They are shown in the ascending
       order of their position numbers.

.. _central-extended-attrs-data-type-tab:

Extended attributes - Data type tab
-----------------------------------

.. _central-extended-attrs-data-type-tab-table:

.. list-table:: *Data type* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Syntax class
     - When values are entered in UMC modules, a syntax check is performed.

       Apart from standard syntax definitions (``string``) and (``integer``),
       there are three possibilities for expressing a binary condition. The
       syntax ``TrueFalse`` is represented at LDAP level using the strings
       ``true`` and ``false``, the syntax ``TrueFalseUpper`` corresponds to the
       OpenLDAP boolean values ``TRUE`` and ``FALSE`` and the syntax ``boolean``
       does not save any value or the string *1*.

       The syntax ``string`` is the default. An overview of the additionally
       available syntax definitions and instructions on integrating your own
       syntax can be found in :cite:t:`developer-reference`.

   * - Default value
     - If a preset value is defined here, new objects to be created will be
       initialized with this value. The value can still be edited manually
       during creation. Existing objects remain unchanged.

   * - Multi value
     - This option establishes whether a single value or multiple values can be
       entered in the input mask. The scheme definition of the LDAP attribute
       specifies whether one or several instances of the attribute may be used
       in one LDAP object.

   * - Value required
     - If this option is active, a valid value must be entered for the extended
       attribute in order to create or save the object in question.

   * - Editable after creation
     - This option establishes whether the object saved in the extended
       attribute can only be modified when saving the object, or whether it can
       also be modified subsequently.

   * - Value is only managed internally
     - If this option is activated, the attribute cannot be modified manually,
       neither at creation time, nor later. This is useful for internal state
       information configured through a hook function or internally inside a
       module.

   * - Copyable
     - Values of this extended attribute are automatically filled into the form
       when copying a object.
