# Preface: Stuff to watch out for when developing frontend
- Disable caching in the network tab of the browser dev console
- adblocker
	- when using `make build-dev` for `univention-web` the frontend might not work correctly
      if you have an ad-blocker active in your browser. Symptoms can be UMC modules not opening
      or the login not finishing for example.

# Development of dojo based web interfaces

An UCS system provides several web interfaces that are built with the
[Dojo Toolkit](https://docs.software-univention.de/architecture/5.0/en/appendix/third-party.html#term-Dojo-Toolkit)
JavaScript framework.

These web interfaces are:
- /univention/login - The login page for all web interfaces of a UCS system.
- /univention/management - The [UMC - Univention Management Console](https://docs.software-univention.de/architecture/5.0/en/services/umc.html#).
- /univention/server-overview - A web interface, showing all UCS systems of the domain.
- /univention/setup - The web based configuration wizard while installing a UCS system.

This document explains how to develop for these Dojo-based web interfaces.

## Getting a UCS system

For development you need a running UCS system.
See the [Development environment](https://univention.gitpages.knut.univention.de/internal/dev-handbook/dev-env.html)
section in "Handbook for Univention Development Department" on how to create a UCS system.

## General setup of our Dojo-Toolkit-based web interfaces

Let's look at a generalised `index.html` file for a Dojo-Toolkit-based web interface.

The `<body>` tag:

The `<body>` tag is mostly an empty shell since the majority of the rendering is made with JavaScript, but it
can contain various degrees of initial HTML. The minimum of overlapping HTML are 2 parts.


```html
<body class="umc">
	<!-- Some node used as the starting point for rendering via JavaScript -->
	<div id="content" class="container"></div>

	<!-- The web interfaces use JavaScript to render and update the DOM so they are not usable with JavaScript disabled -->
	<noscript>
		<div class="nojs__warningWrapper">
			<h1 class="nojs__warning__header">Welcome to Univention Corporate Server</h1>
			<div class="nojs__warning umcCard2">
				<svg class="nojs__warning__icon" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><use xlink:href="/univention/js/dijit/themes/umc/images/info.svg#info"/></svg>
				<div>
					<h2 class="nojs__warning__title">JavaScript required</h2>
					<p>A browser with JavaScript enabled is required in order to use this service.</p>
					<p>When using Internet Explorer, please check your security settings and add this address to your trusted sites.</p>
				</div>
			</div>
		</div>
	</noscript>
</body>
```

The `<head>` tag:

The `<head>` tag contains the usual suspects like the `<title>`, favicon and `<meta>` information but let's
focus on the setup of the Dojo Toolkit framework for now.

First of, we don't use a Dojo Toolkit version directly. In the `univention/dev/ucs` repository under
[management/univention-dojo](https://git.knut.univention.de/univention/dev/ucs/-/tree/5.0-6/management/univention-dojo?ref_type=heads)
we take a base Dojo Toolkit version and apply some patches and add some additional libraries.

The resulting package is used as a dependency for
[univention-web](https://git.knut.univention.de/univention/dev/ucs/-/tree/5.0-6/management/univention-web?ref_type=heads),
our JavaScript library on top of Dojo Toolkit.

`univention-web` produces 5 artifacts that we use in the `<head>` tag to setup the web interface:
- config.js - A file to create generalised `umcConfig` and `dojoConfig` objects which configure the
              behaviour of our web interfaces and the
              [Dojo Loader](https://dojotoolkit.org/reference-guide/1.8/loader/amd.html#configuration-feature-detection)
              respectively.
- dojo.js - A compiled file containing the Dojo Toolkit, libraries from `univention-dojo` and our JavaScript tools
            and widgets from `univention-web`.
- umc.css - A single CSS for everything inside dojo.js and some additional styles used across the web interfaces.
- dark.css and light.css - CSS files defining a theme for the web interfaces.


```html
<head>
	<!-- [...] omitted some tags <meta>, <title>, favicon [...] -->

	<!-- CSS for univention-web -->
	<link rel="stylesheet" href="/univention/js/dijit/themes/umc/umc.css" type="text/css"/>

	<!-- theme.css is a symlink to either dark.css or light.css. Or a customer defined theme. -->
	<link rel="stylesheet" href="/univention/theme.css" type="text/css"/>

	<!-- Extra CSS for the current web interface -->
	<link rel="stylesheet" href="/univention/setup/style.css">

	<script type="text/javascript">
		<!-- Before loading `config.js` below we can predefine `umcConfig` and `dojoConfig` -->
		<!-- `callback` can be seen as an entry point, after everything has loaded. -->
		var umcConfig = {
			loadMenu: false,
			autoLogin: false,
			deps: ["setup"],
			callback: function(setup) {
				setup.start({
					username: getQuery('username'),
					password: getQuery('password')
				});
			}
		};
	</script>
	<!-- Initialise configs for Dojo Toolkit and our web interfaces -->
	<script type="text/javascript" src="/univention/js/config.js"></script>
	<script type="text/javascript">
		<!-- We can alter `umcConfig` and `dojoConfig` defined in `config.js` above here -->
	</script>

	<!-- Load the framework using `umcConfig` and `dojoConfig` defined in `config.js` above -->
	<script type="text/javascript" async src="/univention/js/dojo/dojo.js"></script>
</head>
```


## Dev setup for univention-web

If you want to make changes to univention-web and test them on your UCS system you could just copy it over
and install it:

```bash
cd univention-web && apt-get -y build-dep . && dpkg-buildpackage -us -uc && dpkg -i ../*.deb
```

But this takes a long time (~5min). A faster way is to run `make build-dev`:

```bash
# Copy the `univention-web` folder to your UCS system.
rsync -r /path/to/univention-web/ <ip-of-my-ucs-system>:/home/univention-web/

# WARNING: If you copy `univention-web` to `/root/`, you have to call
#          `chmod +x /root`, otherwise the frontend will not work properly.

# On the UCS system go to where you copied `univention-web` to.
cd /home/univention-web

# Install needed dependencies
apt-get build-dep .

# Call `make build-dev` (build-dev is defined in univention-web/Makefile).
# This will compile all stylus files to the final CSS output and create
# symlinks for all JavaScript files.
make build-dev

# WARNING: When using 'make build-dev' the frontend might not work correctly
#          when you have an ad-blocker active in your browser.

# If you want to see new changes since the last `make build-dev` call,
# just copy univention-web over again.
rsync -r /path/to/univention-web <ip-of-my-ucs-system>:/home/univention-web/

# If you make CSS changes or add new JavaScript files you have to
# call `make clean` to erase the previous `make build-dev` and
# then call 'make build-dev' again.
# Otherwise you can omit this step.
make clean; make build-dev

# To revert to the installed `univention-web` version on the UCS system
# you can call `make clean`.
make clean
```

## System setup (/var/www/univention/setup)

The system setup is the web-based configuration wizard while installing an UCS system.
You can see some screenshots of it in the
[Univention Corporate Server - Manual for users and administrators](https://docs.software-univention.de/manual/5.0/en/installation.html#domain-settings).

The code for the system setup can be found here:
[univention-system-setup](https://git.knut.univention.de/univention/dev/ucs/-/tree/5.0-6/base/univention-system-setup?ref_type=heads).

The directory also defines other frontend-related packages like "univention-managment-console-setup".
But for the web-based configuration wizard we want to look at the "univention-system-setup" package.

The frontend files for "univention-system-setup" can be found under
`univention-system-setup/usr/share/univention-system-setup/www`.

You can access the system setup on an already installed UCS system by setting the
`system/setup/boot/start` UCR variable to `true` and
reloading the apache service `service apache2 reload`.

```bash
ucr set system/setup/boot/start='true'
service apache2 reload
```

You can now access the system setup via https://<ip-of-you-ucs-system>/univention/setup.

Beware that going through the system setup on an installed UCS system will still
apply changes to that system.
E.g. changing the IP address and clicking on next.

You can circumvent that by skipping to pages via the browser dev console.
Here are some non-exhaustive commands that can be useful for debugging/developing:


```javascript
// get a reference to the ApplianceWizard.js instance
w = dijit.byId('setupApplianceWizard')

// list all pages in order of appearence
w.pages.forEach(p => console.log(p.name))

// select one of those pages
// w.selectChild(w._pages[pagename])
w.selectChild(w._pages['network'])

// update buttons of the page which does not happen automatically if we skip to it
// w._updateButtons(pagename)
w._updateButtons('network')

// add information to the error page
w._updateErrorPage(["foo", "bar"])
```

To develop the system setup frontend you can just copy your changed files to
`/var/www/univention/setup` on your UCS system.

For CSS changes you have to compile `style.styl` file first to `style.css`:

```bash
stylus style.styl
```

`stylus` cli can be installed via:
```bash
apt install node-stylus
```

## Server overview (/var/www/univention/server-overview)

The server overview shows all UCS systems of the domain.

The source code for the frontend files can be found here:
[univention-server-overview](https://git.knut.univention.de/univention/dev/ucs/-/tree/5.0-6/management/univention-server-overview/www?ref_type=heads).

To develop the server-overview frontend you can just copy changes under
`univention-server-overview/www/` to
`/var/www/univention/server-overview` on your UCS system.

For CSS changes you have to compile `style.styl` file first to `style.css`:

```bash
stylus style.styl
```

`stylus` cli can be installed via:
```bash
apt install node-stylus
```

## Login (/var/www/univention/login)

A shared login page for multiple web interfaces.

The source code for the frontend files can be found here:
[univention-management-console](https://git.knut.univention.de/univention/dev/ucs/-/tree/5.0-6/management/univention-management-console/www/login?ref_type=heads).

To develop the login frontend you can just copy changes under
`univention-management-console/www/login/` to
`/var/www/univention/login` on your UCS system.

An exception is the CSS for the login page.
The style for the login is not defined in `univention-management-console`.
It is defined in [univention-web/css/login.styl](https://git.knut.univention.de/univention/dev/ucs/-/blob/5.0-6/management/univention-web/css/login.styl?ref_type=heads).

You can either follow the [Dev setup for univention-web](#dev-setup-for-univention-web) to apply your changes to `login.styl`
on your UCS system or just compile `login.styl` and copy it to the correct location.

```bash
stylus login.styl

scp login.css <ip-of-your-ucs-stytem>:/usr/share/univention-web/js/dijit/themes/umc/login.css
```

## UMC - Univention Management Console (/var/www/univention/management)

The UMC is the web interface for the management of a UCS system.

The frontend of the UMC consists of two parts, the UMC itself and UMC modules:
- The UMC itself - A web interface acting as the shell/host for loading and displaying UMC modules
- UMC modules - JavaScript modules that can be loaded by the UMC and provide all the business functionality.

For an architecture overview of the UMC you can read [Architecture documentation](https://docs.software-univention.de/architecture/5.0/en/services/umc.html#).

For the development of the backend and package related things of the UMC and UMC modules
you can read the [Manual for developers](https://docs.software-univention.de/developer-reference/5.0/en/umc/index.html#).

### UMC

The source code for the frontend files of the UMC can be found here:
[univention-management-console](https://git.knut.univention.de/univention/dev/ucs/-/tree/5.0-6/management/univention-management-console/www/management?ref_type=heads).

To develop the UMC you can just copy changes under
`univention-management-console/www/management/` to
`/var/www/univention/management` on your UCS system.

You might have noticed when reading the
[Manual for users and administrators](https://docs.software-univention.de/manual/5.0/en/central-management-umc/umc.html#)
that the UMC itself is not mentioned but only the UMC modules.
That is because the direct usage of the UMC (/var/www/univention/management) is somewhat deprecated.
The UMC modules are still loaded via the UMC but the web interface to access them is the
[UCS Portal](https://docs.software-univention.de/manual/5.0/en/central-management-umc/portal.html#central-portal).

### UMC modules

The source code for the UMC modules of a basic UCS system are listed in the
[Architecture documentation for UMC](https://docs.software-univention.de/architecture/5.0/en/services/umc.html).

Installed apps might provide additional UMC modules like the UCS@school app.

The frontend files for UMC modules are always in the `umc/js` folder of the module.

All UMC modules are installed to
`/usr/share/univention-management-console-frontend/js/umc/modules`
on an UCS system.

To develop the frontend you can just copy the files from `umc/js` to
`/usr/share/univention-management-console-frontend/js/umc/modules`
on your UCS system.
