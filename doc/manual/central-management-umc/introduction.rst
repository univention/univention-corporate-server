.. _central-management-umc-introduction:

Introduction
============

.. _central-access:

Access
------

The |UCSWEB| can be opened on any UCS system via the URL
:samp:`https://{servername}/`. Alternatively, access is also possible via the server's
IP address. Under certain circumstances it may be necessary to access the
services over an insecure connection (e.g., if no SSL certificates have been
created for the system yet). In this case, ``http`` must be used instead of
``https`` in the URL. In this case, passwords are sent over the network in plain
text!

.. _central-browser-compatibility:

Browser compatibility
---------------------

The |UCSWEB| uses numerous JavaScript and CSS functions. Cookies need to be
permitted in the browser. The following browsers are supported:

* :program:`Chrome` as of version 85

* :program:`Firefox` as of version 78

* :program:`Microsoft Edge` as of version 88

* :program:`Safari` and :program:`Safari Mobile` as of version 13

Users with older browsers may experience display problems or the site does not
work at all.

The |UCSWEB| is available in German and English (and French if it is chosen as
language during the installation from DVD); the language to be used can be
changed via the entry :guilabel:`Switch language` of the user menu in the upper
right corner.

.. _central-theming:

Switching between dark and light theme for |UCSWEB|\ s
------------------------------------------------------

All |UCSWEB|\ s have a dark and a light theme that can be switched between with
the |UCSUCRV| :envvar:`ucs/web/theme`. The value of :envvar:`ucs/web/theme`
corresponds to a CSS file under :file:`/usr/share/univention-web/themes/` with
the same name (without file extension). For example, setting
:envvar:`ucs/web/theme` to ``light`` will use
:file:`/usr/share/univention-web/themes/light.css` as theme for all |UCSWEB|\ s.

.. _central-theming-custom:

Creating a custom theme/Adjusting the design of |UCSWEB|\ s
-----------------------------------------------------------

To create a custom theme it is advised not to edit
:file:`/usr/share/univention-web/themes/dark.css` or
:file:`/usr/share/univention-web/themes/light.css` since
the changes may be overwritten when upgrading UCS. Instead copy one of
these files to e.g.
:file:`/usr/share/univention-web/themes/mytheme.css` and
set the |UCSUCRV| :envvar:`ucs/web/theme` to
``mytheme``.

The files :file:`/usr/share/univention-web/themes/dark.css` and
:file:`/usr/share/univention-web/themes/light.css` contain the same list of `CSS
variables <mozilla-css-custom-properties_>`_. These variables are used in other
CSS files and are the supported layer of configurability for |UCSWEB|\ s. The
names and current use case for these variables will not change between UCS
upgrades but new ones may be added.

Some |UCSWEB|\ s import their own local :file:`custom.css` file which can be
used to further adjust the design of that page. These are
:file:`/usr/share/univention-management-console-login/css/custom.css`
(:ref:`domain-saml-sso-login`) and
:file:`/usr/share/univention-portal/custom.css` (:ref:`central-portal`). The
files are empty when installing UCS and are not modified when installing any UCS
update. Be aware though that a given `CSS selector <mozilla-css-selectors_>`_
may break when installing any UCS update.

.. _central-management-umc-feedback:

Feedback on UCS
---------------

By choosing the :menuselection:`Help --> Feedback` option in the upper right
menu, you can provide feedback on UCS via a web form.

.. _central-management-umc-matomo:

Collection of usage statistics
------------------------------

Anonymous usage statistics on the use of the |UCSWEB| are collected when using
the *core edition* version of UCS (which is generally used for evaluating UCS).
Further information can be found in :uv:kb:`Data collection in Univention
Corporate Server <6701>`.
