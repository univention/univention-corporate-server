https://raw.github.com/wkeese/api-viewer/master/README.rst

Manual install for the DTK API documentation tool
--------------------------------------------------

Requirements:

* PHP 5.2 or higher

* Apache with mod_rewrite enabled


Generating the documentation and running API viewer locally
-----------------------------------------------------------

1. get latest Node.js from http://nodejs.org/#download

2. check out js-doc-parse from bill (it has various fixes/enhancements needed for the viewer)::

    $ git clone --recursive https://github.com/wkeese/js-doc-parse.git
    $ cd js-doc-parse
    $ git checkout all-my-changes

3. edit config.js to give path to dojo (your path may vary from example below):

MacOS::

    environmentConfig: {
        basePath: '../trunk/',
        packages: {
            dojo: 'dojo',
            dijit: 'dijit',
            dojox: 'dojox',
            doh: 'util/doh'
        },
        // ...
    }

Windows::

	environmentConfig: {
		basePath: 'c:\\users\\me\\trunk\\',
		packages: {
			dojo: 'dojo',
			dijit: 'dijit',
			dojox: 'dojox',
			doh: 'util/doh'
		},
		// ...
		excludePaths: {
            // ...
            /\\(?:tests|nls|demos)\\/,
            // ...
		}
	}

4. run parser on ``dojo`` source

MacOS::

    $ ./parse.sh ../trunk/dojo ../trunk/dijit ../trunk/dojox

Windows::

    C:\> parse.bat c:\\users\\me\\trunk

This will generate ``details.xml`` and ``tree.json``.

5. check out api-viewer

Check out this project into a directory called "api", under your web root, so that it's accessible via
http://localhost/api:

    $ cd `your web root`
    $ git clone git@github.com:wkeese/api-viewer.git api

If you put it in a different location instead, then you need to update config.php and .htaccess to point
to the other location.

6. move files to data directory

Create ``api_data/1.8`` directory (or whatever the current version is), as a *sibling* of the api directory,
and move the ``details.xml`` and ``tree.json`` from the step #4 above to that directory.

Alternately, you can set the directory to somewhere else by editing config.php.



Instructions to run the site
----------------------------

1. Create a virtual host in Apache, and allow Overrides in the definition.

2. Place the entire API site in the directory where you are pointing the vhost.

3. Set the permissions on the /data directory to be writable; it should have the ability to not only write directly to that directory, but to also create sub-directories and write to them as well.  To do this on Mac OS X::

    $ chmod -R +a 'user:_www allow delete,list,search,add_file,add_subdirectory,read,write' data

4. Open the config.php file, and edit with your specific information (including the ``_base_url`` variable; leave this to be ``/`` if you are running in the root of a vhost).  Note that modules to be displayed should all have a value of ``-1`` (this is set by the class tree generator), and should be in the order in which you want the modules to appear within the class tree.

5. If you are just running the site with the included XML files, that should be all there is to running the site; just hit your vhost and go.


Theming your API documentation tool
-----------------------------------

Themes are located in in the ``themes`` directory.  The require, at a minimum:

* theme.css - Includes any CSS styling that needs to be included in the doucment

* index.php - The content is used to populate the *Welcome* tab of the API Viewer

* header.php - Inserted before the main content area

* footer.php - Inserted after the main content area

These files will be included as the pages are generated.


Implementation Notes
--------------------

PHP files:

- generate.php - utility methods

- spider.php - used to pre-cache web static HTML versions of pages

The data files are:

- details.xml - main information about modules

- tree.json - just the metadata needed to display the tree of modules
