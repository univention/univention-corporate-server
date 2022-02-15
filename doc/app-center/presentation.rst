.. _app-presentation:

App presentation
================

This chapter is about how the app is presented to the user with texts,
logos, screenshots and videos. The contents are part of the app
configuration. They are shown to the UCS system administrator in the App
Center UMC module in UCS and to users on the Univention website in the
`App
Catalog <https://www.univention.com/products/univention-app-center/app-catalog/>`_.

All changes are made in the App Provider portal. They need to be saved
by pressing the button :guilabel:`Save`. Then a release can be requested via the
button :guilabel:`Approve for release`. The items mentioned in this chapter can be
changed and published any time and do not require a new version of the
app.

.. _logos:

Logos
-----

All logos uploaded to the App Provider Portal have to be SVG format,
which is most flexible for the presentation purposes.

.. important::

   When SVG files are created or exported, please make sure that fonts
   are converted to paths before export. Otherwise the text in the logos
   is not rendered properly and the logo may look odd.

   Please also do not simply import a bitmap graphic into SVG and export
   it. Results after scaling may not look good, because the logo is
   basically a bitmap in SVG apparel.

The logos can be uploaded on the :guilabel:`Presentation` tab in the *Logos* section.
Two icons are needed: One for the app tile on the overview page and a
more detailed logo for the app page. The tile has only limited space in
square format. Please make sure, the logo can still be recognized. The
detailed logo is not limited. Most logos for this slot have a landscape
orientation. The App Center and the App Catalog take care of the
appropriate scaling. SVG allows a very good result due to its nature as
a vector graphics format.

.. _screentshots:

Screenshots and videos
----------------------

Screenshots and videos are a good way to introduce the solution to the
user. To add screenshots please go to the :guilabel:`Screenshots & YouTube videos`
section on the :guilabel:`Presentation` tab. Screenshots can be in PNG or JPG
format. Videos have to be published on YouTube and the full YouTube link
has to be provided in the App Provider Portal. Please keep in mind to
provide the material for English and German speaking audience.

If the same screenshots exist in German, it is recommended that they are
added, as well.

Comprehensive visualizations can be added optionally which make it
easier to understand the app's description. Give the image files
sensible names including the keywords. An example of a bad file name for
an image would be :file:`app_76bz3.jpg`, whereas :file:`app_name.jpg` would be
much better.

.. _description:

Description
-----------

The full description is the text introducing the solution to the user
and thus is very important for getting their attention. Here are some
tips intended to help to present the app in a user-friendly,
customer-oriented, and search-engine-optimized manner.

*  Unique content with at least 300 words. Not a copy from the solutions
   web page.

*  Content: What does the app do? The added value and benefits should be
   described and examples be provided.

*  The app is running on UCS. What is the added value that the
   combination of UCS and the app offers to the customer?

*  It is important for the user to understand which "edition" of the
   solution is installed and what features or limitations are included.
   Please also provide information on how to "upgrade" to the next
   "edition".

*  The text should be structured in paragraphs. Subheadings and lists
   should be used.

*  Search engines should be kept in mind and keywords be used.

*  Links should be furnished with all HTML attributes.

*  Include supporting images/screenshots and define them in the app
   configuration (not within description).

The description is provided in HTML format. If more control on the HTML
is needed, switch to HTML source mode and edit the HTML directly. Here
sections and headings can be added.

.. note::

   Custom styles in CSS should not be used, because they may distract
   from the overall impression. The App Center UMC module and the App
   Catalog already have respective CSS style definitions.

The length of the description depends on how much there is to say and
how much explanation the app requires. Ideally the description should be
at least 300 words long. The text should be structured and paragraphs
should be used to make it easier to read. The target group are potential
customers. Subheadings (HTML: *h2*, *h3*) should be used to divide the
text into logical sections. It is very helpful for the reader to be able
to see the advantages of the app and its combination with UCS at a
glance. For this reason, presentation of the advantages in lists (HTML:
*ol*, *ul*, *li*) is particularly practical.

If links are used in the app description (e.g., to pages on the
solution's own website), please always use the ``target="_blank"`` (open
in new tab) and assign the link a title attribute. Please keep the use
of links to a minimum and ideally use the fields provided especially for
this purpose in the app metadata.

.. _category:

Categories
----------

On the :guilabel:`Presentation` tab the app can be given one or more categories from
a given set in the *App categories* section. Users can filter the app
overview in the App Center and in the App Catalog accordingly. App
categories help to group apps together by topic and give a better
overview for the various apps available.

Contact
-------

For the users it is important to know who is the producer of the app.
For this purpose there is the *Responsibility: Contact information*
section on the :guilabel:`Presentation` tab in the App Provider Portal. Please
provide product contact information like an email address and a website
to the solution. Please also link to a website, where the app provider's
support options and pricing is explained to potential customers and
place the link in the field Link to website with product support
options.

License
-------

In the *License* section on the :guilabel:`Presentation` tab license information can
be defined; for example, a license agreement. This has to be read and
accepted by a UCS system administrator before the app is installed. If
the text is not accepted, the installation process is aborted and no app
is installed. The license agreement is mostly used by app providers for
legal information that needs confirmation by the administrator before
anything is installed. If such a text is not needed, leave it empty.

UCS system administrators have to register with a valid email address in
order to use the App Center. If the app provider configures an email
address in the field :guilabel:`E-mail address for App install notifications` it
receives information on a daily basis about who installed the app. The
App Center UMC module informs the user that the app provider may contact
them. App providers can use the address, for example, for lead
management.

The last setting is intended to provide the users a rough imagination
about the license type of the software. One option best fitting to the
solution should be chosen:

*  ``Empty``: If no value is given, the App Center UMC module and the
   App Catalog will show the text "Please contact the App provider for
   further license details".

*  ``Free commercial use``

*  ``Free commercial use. Some functions or services are liable to costs.``

*  ``Liable to Costs with Free Trial``

*  ``Liable to Costs``

.. _readme:

README for the administrator
----------------------------

In the tab :guilabel:`Additional texts` further information for an app can be
provided that show up at certain stages of the app life cycle. Those
README files are also in HTML like the description and content can be
provided the same way (see :ref:`description`). The App
Provider Portal describes when each README file shows up.

It is highly recommended to use the README files to show information
that should not go in the app description, like for example
configuration details, hints before and after an update, etc. Please
also keep in mind to provide a proper German translation.

.. _translation:

Translations
------------

All texts, screenshots and videos should be entered in English.
Translations to German should be only made in the appropriate field next
to the English text. It should be made sure that translations for the
texts that have an English version are provided. Otherwise, English text
will show up for a user with German language settings.

.. _recommended-apps:

Recommended Apps Badge
----------------------

Apps can be awarded with different badges and are therefore especially
highlighted in the App Center. One of those badges is the `"Recommended
Apps" <https://www.univention.com/products/univention-app-center/app-catalog/?recommended_app=1>`_
award for the use in professional environments. Apps with the
"Recommended Apps" award meet the below listed quality criteria. The
functional scope of the software solution is not evaluated. The award is
assigned by the |UCSAPPC| Team and the criteria serve as decision
guidelines.

*  The app can be installed and uninstalled cleanly and does not alter
   the UCS system against the rules.

*  Univention is not aware of any open security vulnerabilities for the
   app or the app provider has promised to remedy the vulnerabilities
   soon. In principle, Univention does not carry out any active security
   monitoring for apps in the App Center. If Univention becomes aware of
   security vulnerabilities, the App provider will be informed and a
   deadline for an update will be agreed upon.

*  The version of the software solution offered in the App Center is
   maintained by the app provider.

*  If the software solution requires user accounts to identify users,
   the app uses UCS Identity Management as a source of user accounts.

*  The app provider makes updates of its software for the app available
   regularly and promptly to UCS via the App Center.

*  If the app provider offers update paths for its software solution,
   the app also supports these update paths.

*  The app vendor ensures that the app deploys its software solution to
   new UCS versions within a short period of time, ensuring that
   administrators can update UCS.

*  Commercial support is available for the app.

*  The app has been available in the App Center for at least 3 months.

*  For the app, there are virtual app appliances that are linked on the
   app vendor's website for download. This makes commissioning the app
   on UCS extremely easy.


