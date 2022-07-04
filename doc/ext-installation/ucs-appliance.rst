.. _appliance-use:

*********************
Using a UCS appliance
*********************

In addition to the traditional installation, there is also the possibility of
providing UCS via an appliance image. These appliance images can be used both
for simple commissioning in a virtualization solution such as VMware and for
providing a cloud instance.

Appliances can be created with minimal effort. This is described in
:ref:`appliance-create`.

Whilst some of the settings can be preconfigured globally in the image, it is
still necessary for the end user to make final adjustments to the configuration,
e.g., to set the computer name or the domain used. For this reason, a basic
system is installed for the appliance image and a component set up, which then
allows the end user to finalize the configuration. Alternatively, the
configuration can also be performed automatically without user interaction. This
is described in :ref:`appliance-use-auto`.

The interactive configuration can be performed in two ways:

* A graphic interface starts on the system, in which the web browser Firefox is
  started in full-screen mode and automatically accesses the configuration URL.
  This option is particularly suitable for images in virtualization solutions.

* The configuration can also be performed directly via an external web browser.
  In this case, the system's IP address must be known to the user (e.g., if it
  has been notified to him in advance in the scope of the provision of a cloud
  image).

In the scope of the initial configuration, the user can change the following
settings in the default setting:

* Selection of the language, time zone and keyboard layout

* Configuration of the network settings

* Setup of a new UCS domain or joining a UCS or Microsoft Active Directory
  domain

* Software selection of UCS key components. The user can install software from
  other vendors at a later point in time via the Univention App Center.
