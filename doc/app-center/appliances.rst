.. _appliances:

App Appliances
==============

App Appliances are pre-defined images which consist of the App, the UCS
management system and the UCS runtime environment. They are run as a
virtual machine within a hypervisor and are currently provided as
VMware, VMware ESXi, VirtualBox and KVM images. By default the UCS
branding is used, but it is possible and recommended to use a custom
branding.

.. _app-appliances-create:

Create an app appliance
-----------------------

To create an appliance, select an app version that has already been
published and activate the :guilabel:`Create App appliance` checkbox on the
:guilabel:`Appliance` tab. If the solution needs a minimum size of memory, please
specify the needed mega bytes.

.. _appliance-additional-software:

Additional software
~~~~~~~~~~~~~~~~~~~

If the appliance should include additional apps, please specify them in
the *Additional software* section.

.. _appliance-customize-setup-wizard:

Customize setup wizard in appliance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The appliance allows customization of the UCS setup wizard and controls
which setup pages and setup fields should be hidden. For simplicity
towards the user, it is recommended to hide the ``software`` page.

.. _appliance-customize-app-center:

Customize app listing in App Center
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The listing of apps in the App Center UMC module in the appliance can be
customized to either whitelist or blacklist certain apps. For example,
if the solution is a groupware, other groupware solutions can be hidden
from the overview listing. System administrators can only install the
whitelisted apps or are not allowed to install the black listed apps.

.. _appliance-first-steps:

First steps information
~~~~~~~~~~~~~~~~~~~~~~~

The appliances are usually configured in such a way that the user can
start using them right away. In some cases it may be necessary to
provide some information for the first steps. For example, the user
needs to know that a user object has to be created and activated for the
app first. This could be briefly described in this section. The German
translation should be kept in mind and provided.

.. _appliance-umc-favorites:

Customize UMC favorite category
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The appliance also allows to customize the UMC modules which should be
pre-configured for the favorites section in the UCS management system.
The favorites section comes up first, after a UCS system administrator
logs onto the UCS management system. It is recommended to have the
modules ``Users``, ``Groups`` and ``App Center`` listed here.

.. _appliance-build:

Appliance build
~~~~~~~~~~~~~~~

As soon as the settings are made, :guilabel:`Save`, click the :guilabel:`Approve for release`
button and provide a custom message to let the Univention team know that
an appliance is ready to be build. This will create a ticket which helps
to keep the communication in one place.

.. _appliance-release:

Test and release
~~~~~~~~~~~~~~~~

The appliance is automatically built in the Univention build
infrastructure. After the build is finished, automatic tests will be
started. Build and testing will approximately need four hours.

After the automatic tests have finished successfully, the app provider
is informed. A link to the appliance download is sent and a few days are
given for testing. If no veto is sent, the Appliance is usually
published after the veto deadline. After the release, the appliance will
show up for download on the app page in the App Catalog. App Providers
are recommended to also place a link to the app detail page from their
download page. The link is one criteria for the recommended apps badge
in the App Center overview and the App Catalog.

.. _branding:

Custom branding
---------------

With a customized branding of an appliance the boot loader, the boot
splash, the system setup wizard and the portal page can be modified.
Please look at the screenshots below and the explanations of the options
that control the look.

.. _appliance-branding-bootloader:

Boot loader
~~~~~~~~~~~

The background color can be configured for the boot loader. Please
define in the *Primary color* setting.

.. _appliance-branding-bootloader-figure:

.. figure:: /images/Appliance_Branding_Bootloader.png
   :alt: Boot loader

   Boot loader

.. _appliance-branding-bootsplash:

Boot splash
~~~~~~~~~~~

The boot splash can have a custom background and a logo. The logo is
defined in *Logo for the bootsplash during system boot*. Please provide a
SVG file and mind the recommendations in :ref:`Logos <logos>`.

The background color is defined in *CSS definition of the appliance
background in bootsplash & welcome screen*. For a black background,
simply define ``#000000``. A gradient can for example be defined with
``linear-gradient(to bottom, #345279 0%, #1d2c41 100%)``. For more
information on how to use a gradient, see `CSS linear-gradient()
function on w3schools <css-linear-gradient_>`_.

.. _appliance-branding-bootsplash-figure:

.. figure:: /images/Appliance_Branding_Bootsplash.png
   :alt: Boot splash

   Boot splash

.. _appliance-branding-setup-wizard:

System setup wizard
~~~~~~~~~~~~~~~~~~~

The system setup wizard allows several slots to be customized. In the
*Configuration* section in the App Provider Portal, the ``Appliance name``
(the word "appliance" is automatically appended) can be set. It controls
the heading in the system setup wizard. The *Logo for the first page of
the setup wizard* shows up on the first page of the system setup wizard.

In the *Branding* section, the logo on the top left can be changed with
the *Logo for header in setup wizard* setting. The *Primary color* controls
the background color of the UMC header.

The *Secondary color* is used as color for smaller graphical elements
throughout the setup wizard (see :ref:`appliance-branding-umc-branding-figure`).

.. _appliance-branding-setup-wizard-figure:

.. figure:: /images/Appliance_Branding_Setup_Wizard.png
   :alt: System setup first screen

   System setup first screen


.. _appliance-branding-umc-branding-figure:

.. figure:: /images/Appliance_Branding_UMC.png
   :alt: System setup summary screen

   System setup summary screen

.. _appliance-branding-welcome-screen:

Welcome screen
~~~~~~~~~~~~~~

The welcome screen is shown after the appliance setup has been finished
and also every time the appliance is started. It offers information on
how the user can access the appliance. It uses settings like the
Appliance name and the CSS definition of the appliance background. The
*Logo for the welcome screen* needs to be a SVG file that is slightly
wider than high and which has the fonts converted to paths. Please mind
the recommendations in :ref:`Logos <logos>`.

Depending on the character of the welcome screen background (bright or
dark), the *Font color for welcome screen* should be either set to
``White`` or ``Black``.

.. _appliance-branding-umc-branding-welcome-screen:

.. figure:: /images/Appliance_Branding_Welcome_Screen.png
   :alt: Appliance welcome screen

   Appliance welcome screen

.. _appliance-branding-portal-page:

Portal page
~~~~~~~~~~~

The branding of the portal page is independent from the other sections.
The *Title for the UCS portal page in the appliance* can be defined and it
can be configured if the font color shall be black or white. The *Logo
for the portal page* controls which logo shall be set in the first tile
on the portal page. The background can either consist of a background
image or a background color or a background color gradient as described
in :ref:`Boot splash <appliance-branding-bootsplash>`.

.. _appliance-branding-portal-page-figure:

.. figure:: /images/Appliance_Branding_Portal_Page.png
   :alt: Appliance portal page

   Appliance portal page
