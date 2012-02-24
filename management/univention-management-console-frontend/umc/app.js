/*
 * Copyright 2011 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global dojo dijit dojox umc console window */

dojo.provide('umc.app');

dojo.require("dijit.Menu");
dojo.require("dijit.form.Button");
dojo.require("dijit.form.DropDownButton");
dojo.require("dijit.layout.BorderContainer");
dojo.require("dijit.layout.TabContainer");
dojo.require("dojo.cookie");
dojo.require("umc.tools");
dojo.require("umc.dialog");
dojo.require("umc.help");
dojo.require("umc.about");
dojo.require("umc.widgets.CategoryPane");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.Text");
dojo.require("umc.widgets.Button");
dojo.require("umc.i18n");

dojo.mixin(umc.app, new umc.i18n.Mixin({
	// use the framework wide translation file
	i18nClass: 'umc.app'
}), {

	start: function(/*Object*/ props) {
		// summary:
		//		Start the UMC, i.e., render layout, request login for a new session etc.
		// props: Object
		//		The following properties may be given:
		//		* username, password: if both values are given, the UMC tries to directly
		//		  with these credentials.
		//		* module, flavor: if module is given, the module is started immediately,
		//		  flavor is optional.
		//		* overview: if false and a module is given for autostart, the overview will 
		//		  not been shown and the module cannot be closed
		//		* displayUsername: whether or not the username should be displayed
		//		* width: forces the width of the GUI to a specific value

		// save some config properties
		umc.tools.status('width', props.width);
		umc.tools.status('displayUsername', umc.tools.isTrue(props.displayUsername));
		// username will be overriden by final authenticated username
		umc.tools.status('username', props.username);
		// password has been given in the query string... in this case we may cache it, as well
		umc.tools.status('password', props.password);

		if (dojo.isString(props.module)) {
			// a startup module is specified
			var handle = dojo.connect(this, 'onGuiDone', dojo.hitch(this, function() {
				dojo.disconnect(handle);
				this.openModule(props.module, props.flavor);
				this._tabContainer.layout();
				
				// put focus into the CategoryPane for scrolling
				/*dijit.focus(this._categoryPane.domNode);
				this.connect(_categoryPane, 'onShow', function() {
					dijit.focus(this._categoryPane.domNode);
				});*/
			}));

			umc.tools.status('overview', umc.tools.isTrue(props.overview));
		}

		if (props.username && props.password && dojo.isString(props.username) && dojo.isString(props.password)) {
			// username and password are given, try to login directly
			umc.dialog.login().then(dojo.hitch(this, 'onLogin'));
			return;
		}

		// check whether we still have a app cookie
		var sessionCookie = dojo.cookie('UMCSessionId');
		if (undefined === sessionCookie) {
			umc.dialog.login().then(dojo.hitch(this, 'onLogin'));
		}
		else {
			this.onLogin(dojo.cookie('UMCUsername'));
			//console.log(this._('Login is still valid (cookie: %(cookie)s, username: %(user)s).', { cookie: sessionCookie, user: umc.tools.status('username') }));
		}
	},

	onLogin: function(username) {
		// save the username internally and as cookie
		dojo.cookie('UMCUsername', username, { expires: 100, path: '/' });
		umc.tools.status('username', username);

		// set the UCR session timeout value
		umc.tools.ucr('umc/http/session/timeout').then( function(res) {
			umc.tools._sessionTimeout = parseInt( res['umc/http/session/timeout'] , 10 );
		} );

		// start the timer for session checking
		umc.tools.checkSession(true);

		// load the modules
		this.loadModules();
	},

	// _tabContainer:
	//		Internal reference to the TabContainer object
	_tabContainer: null,

	openModule: function(/*String|Object*/ module, /*String?*/ flavor, /*Object?*/ props) {
		// summary:
		//		Open a new tab for the given module.
		// description:
		//		This method is subscribed to the channel '/umc/modules/open' in order to
		//		open modules from other modules without requiring 'umc.app'.
		// module:
		//		Module ID as string
		// props:
		//		Optional properties that are handed over to the module constructor.

		// get the object in case we have a string
		if (typeof(module) == 'string') {
			module = this.getModule(module, flavor);
		}
		if (undefined === module) {
			return;
		}

		// create a new tab
		var params = dojo.mixin({
			title: module.name,
			iconClass: umc.tools.getIconClass(module.icon),
			closable: umc.tools.status('overview'),  // closing tabs is only enabled of the overview is visible
			moduleFlavor: module.flavor,
			moduleID: module.id,
			description: module.description
			//items: [ new module.BaseClass() ],
			//layout: 'fit',
			//closable: true,
			//autoScroll: true
			//autoWidth: true,
			//autoHeight: true
		}, props);
		var tab = new module.BaseClass(params);
		this._tabContainer.addChild(tab);
		this._tabContainer.selectChild(tab, true);
		tab.startup();
	},

	focusTab: function(tab) {
		if (dojo.indexOf(this._tabContainer.getChildren(), tab) >= 0) {
			this._tabContainer.selectChild(tab, true);
		}
	},

	closeTab: function(tab, /*Boolean?*/ destroy) {
		tab.onClose();
		this._tabContainer.removeChild(tab);
		if (destroy === undefined || destroy === true) {
			tab.destroyRecursive();
		}
	},

	onModulesLoaded: function() {
		this.setupGui();
	},

	_modules: [],
	_categories: [],
	_modulesLoaded: false,
	loadModules: function() {
		// make sure that we don't load the modules twice
		if (this._modulesLoaded) {
			this.onModulesLoaded();
			return;
		}

		umc.tools.umcpCommand('get/modules/list', null, false).then(dojo.hitch(this, function(data) {
			// get all categories
			dojo.forEach(dojo.getObject('categories', false, data), dojo.hitch(this, function(icat) {
				this._categories.push(icat);
			}));

			// hack a specific order
			//TODO: remove this hack
			//var cats1 = [];
			//var cats2 = this._categories;
			//dojo.forEach(['favorites', 'ucsschool'], function(id) {
			//	var tmpCats = cats2;
			//	cats2 = [];
			//	dojo.forEach(tmpCats, function(icat) {
			//		if (id == icat.id) {
			//			cats1.push(icat);
			//		}
			//		else {
			//			cats2.push(icat);
			//		}
			//	});
			//});
			//this._categories = cats1.concat(cats2);
			//console.log(cats1);
			//console.log(cats2);
			//console.log(this._categories);
			// end of hack :)

			// get all modules
			dojo.forEach(dojo.getObject('modules', false, data), dojo.hitch( this, function(module) {
				// try to load the module
				try {
					dojo['require']('umc.modules.' + module.id);
				}
				catch (error) {
					// log as warning and continue with the next element in the list
					console.log('WARNING: Loading of module ' + module.id + ' failed. Ignoring it for now!');
					return true;
				}

				// load the module
				// add module config class to internal list of available modules
				this._modules.push(dojo.mixin({
					BaseClass: dojo.getObject('umc.modules.' + module.id)
				}, module));
			}));

			// loading is done
			this.onModulesLoaded();
			this._modulesLoaded = true;
		}), dojo.hitch(this, function(error) {
			umc.dialog.login().then(dojo.hitch(this, 'onLogin'));
		}));
	},

	getModules: function(/*String?*/ category) {
		// summary:
		//		Get modules, either all or the ones for the specific category.
		//		The returned array contains objects with the properties
		//		{ BaseClass, id, title, description, categories }.
		// categoryID:
		//		Optional category name.

		var modules = this._modules;
		if (undefined !== category) {
			// find all modules with the given category
			modules = [];
			for (var imod = 0; imod < this._modules.length; ++imod) {
				// iterate over all categories for the module
				var categories = this._modules[imod].categories;
				for (var icat = 0; icat < categories.length; ++icat) {
					// check whether the category matches the query
					if (category == categories[icat]) {
						modules.push(this._modules[imod]);
						break;
					}
				}
			}
		}

		// return all modules
		return modules; // Object[]
	},

	getModule: function(/*String*/ id, /*String?*/ flavor) {
		// summary:
		//		Get the module object for a given module ID.
		//		The returned object has the following properties:
		//		{ BaseClass, id, description, category, flavor }.
		// id:
		//		Module ID as string.
		// flavor:
		//		The module flavor as string.

		var i;
		for (i = 0; i < this._modules.length; ++i) {
			if (!flavor && this._modules[i].id == id) {
				// flavor is not given, we matched only the module ID
				return this._modules[i]; // Object
			}
			else if (flavor && this._modules[i].id == id && this._modules[i].flavor == flavor) {
				// flavor is given, module ID as well as flavor matched
				return this._modules[i]; // Object
			}
		}
		return undefined; // undefined
	},

	getCategories: function() {
		// summary:
		//		Get all categories as an array. Each entry has the following properties:
		//		{ id, description }.
		return this._categories; // Object[]
	},

	_categoryPane: null,
	setupGui: function() {
		// make sure that we have not build the GUI before
		if (umc.tools.status('setupGui')) {
			return;
		}

		// set up fundamental layout parts
		var topContainer = new dijit.layout.BorderContainer( {
			'class': 'umcTopContainer',
			gutters: false,
			// force a displayed width if specified
			style: umc.tools.status('width') ? 'width:' + umc.tools.status('width') + 'px;' : null 
		}).placeAt(dojo.body());

		// container for all modules tabs
		this._tabContainer = new dijit.layout.TabContainer({
			region: 'center',
			'class': 'umcMainTabContainer'
		});
		topContainer.addChild(this._tabContainer);

		if (umc.tools.status('overview')) {
			// the container for all category panes
			// NOTE: We add the icon here in the first tab, otherwise the tab heights
			//	   will not be computed correctly and future tabs will habe display
			//	   problems.
			//     -> This could probably be fixed by calling layout() after adding a new tab!
			var overviewPage = new umc.widgets.Page({
				title: this._('Overview'),
				headerText: this._('Overview'),
				iconClass: umc.tools.getIconClass('univention'),
				helpText: this._('Univention Management Console (UMC) is the central tool for web-based administration of the UCS domain. It supports the management of domain-wide available data in the LDAP directory, e.g., users, groups or host accounts, and allows the configuration or management of an individual system, e.g., the starting and stopping of services. Depending on system role, default settings and permissions, you find extensive functions for the administration of your UCS domain and for the configuration of this server.')
			});
			this._tabContainer.addChild(overviewPage);

			// get needed UCR variables
			umc.tools.umcpCommand( 'get/ucr', [ 'ssl/validity/days', 'ssl/validity/warning', 'update/available', 'update/reboot/required' ] ).then( dojo.hitch( this, function( data ) {
				// check validity of SSL certificates
				var days = parseInt( data.result[ 'ssl/validity/days' ], 10 );
				var warning = parseInt( data.result[ 'ssl/validity/warning' ], 10 );
				if ( days <= warning ) {
					overviewPage.addNote( this._( 'The SSL certificate will expire in %d days and should be renewed!', days ) );
				}

				// check if updates are available
				if ( umc.modules.updater && umc.tools.isTrue(data.result['update/available']) ) {
					var link = 'href="javascript:void(0)" onclick="umc.app.openModule(\'updater\')"';
					overviewPage.addNote( this._( 'An update for UCS is available. Please visit <a %s>Online Update Module</a> to install the updates.', link ) );
				}

				// check if system reboot is required
				if ( umc.modules.reboot && umc.tools.isTrue(data.result['update/reboot/required']) ) {
					var link_reboot = 'href="javascript:void(0)" onclick="umc.app.openModule(\'reboot\')"';
					overviewPage.addNote( this._( 'This system has been updated recently. Please visit the <a %s>Reboot Module</a> and reboot this system to finish the update.', link_reboot ) );
				}
			}));

			// add a CategoryPane for each category
			var categories = umc.widgets.ContainerWidget({
				scrollable: true
			});
			dojo.forEach(this.getCategories(), dojo.hitch(this, function(icat) {
				// ignore empty categories
				var modules = this.getModules(icat.id);
				if (0 === modules.length) {
					return;
				}

				// create a new category pane for all modules in the given category
				this._categoryPane = new umc.widgets.CategoryPane({
					modules: modules,
					title: icat.name,
					open: true //('favorites' == icat.id)
				});

				// register to requests for opening a module
				dojo.connect(this._categoryPane, 'onOpenModule', dojo.hitch(this, this.openModule));

				// add category pane to overview page
				categories.addChild(this._categoryPane);
			}));
			overviewPage.addChild(categories);
		}

		// the header
		var header = new umc.widgets.ContainerWidget({
			'class': 'umcHeader',
			region: 'top'
		});
		topContainer.addChild( header );

		// we need containers aligned to the left and the right
		var headerLeft = new umc.widgets.ContainerWidget({
			style: 'float: left'
		});
		header.addChild(headerLeft);
		var headerRight = new umc.widgets.ContainerWidget({
			style: 'float: right'
		});
		header.addChild(headerRight);

		// the univention context menu
		var menu = new dijit.Menu({});
		menu.addChild(new dijit.MenuItem({
			label: this._('Help'),
			onClick : function() {
				umc.help.show();
			}
		}));
		if ( this.getModule( 'udm' ) ) {
			dojo['require']( 'umc.modules._udm.LicenseDialog' );
			menu.addChild(new dijit.MenuItem({
				label: this._('License'),
				onClick : function() {
					var dlg = umc.modules._udm.LicenseDialog();
					dlg.show();
				}
			}));
		}
		menu.addChild(new dijit.MenuItem({
			label: this._('About UMC'),
			onClick : function() {
				umc.tools.umcpCommand( 'get/info' ).then( function( data ) {
					umc.about.show( data.result );
				} );
			}
		}));
		menu.addChild(new dijit.MenuSeparator({}));
		menu.addChild(new dijit.MenuItem({
			label: this._('Univention Website'),
			onClick: function() {
				var w = window.open( 'http://www.univention.de/', 'UMC' );
				w.focus();
			}
		}));
		headerLeft.addChild(new dijit.form.DropDownButton({
			'class': 'umcHeaderButton univentionButton',
			iconClass: 'univentionLogo',
			dropDown: menu
		}));

		// query domainname and hostname and add this information to the header
		var hostInfo = new umc.widgets.Text( {
			templateString: '<span dojoAttachPoint="contentNode">${content}</span>',
			content: '...',
			'class': 'umcHeaderText'
		} );
		headerRight.addChild(hostInfo);
		umc.tools.umcpCommand('get/ucr', [ 'domainname', 'hostname' ]).
			then(dojo.hitch(this, function(data) {
				var domainname = data.result.domainname;
				var hostname = data.result.hostname;
				hostInfo.set('content', this._('Host: %(host)s.%(domain)s', {
					domain: domainname,
					host: hostname
				}));

				// save hostname and domainname as status information
				umc.tools.status('domainname', domainname);
				umc.tools.status('hostname', hostname);
			}));

		// the user context menu
		menu = new dijit.Menu({});
		menu.addChild(new dijit.CheckedMenuItem({
			label: this._('Tooltips'),
			checked: umc.tools.preferences('tooltips'),
			onClick: function() {
				umc.tools.preferences('tooltips', this.checked);
			}
		}));
		/*menu.addChild(new dijit.CheckedMenuItem({
			label: this._('Confirmations'),
			checked: true,
			checked: umc.tools.preferences('confirm'),
			onClick: function() {
				umc.tools.preferences('confirm', this.checked);
			}
		}));*/
		menu.addChild(new dijit.CheckedMenuItem({
			label: this._('Module help description'),
			checked: true,
			checked: umc.tools.preferences('moduleHelpText'),
			onClick: function() {
				umc.tools.preferences('moduleHelpText', this.checked);
			}
		}));
		if (umc.tools.status('displayUsername')) {
			headerRight.addChild(new dijit.form.DropDownButton({
				label: this._('User: %s', umc.tools.status('username')),
				'class': 'umcHeaderButton',
				dropDown: menu
			}));
		}

		// add logout button
		headerRight.addChild(new umc.widgets.Button({
			label: '<img src="images/logout.png">',
			'class': 'umcHeaderButton umcLogoutButton',
			onClick: dojo.hitch(this, function() {
				umc.dialog.confirm(this._('Do you really want to logout?'), [{
					label: this._('Logout'),
					auto: true,
					callback: dojo.hitch(this, function() {
						umc.tools.closeSession();
						window.location.reload();
					})
				}, {
					label: this._('Cancel'),
					'default': true
				}]);
			})
		}));

		// put everything together
		topContainer.startup();

		// subscribe to requests for opening modules and closing/focusing tabs
		dojo.subscribe('/umc/modules/open', dojo.hitch(this, 'openModule'));
		dojo.subscribe('/umc/tabs/close', dojo.hitch(this, 'closeTab'));
		dojo.subscribe('/umc/tabs/focus', dojo.hitch(this, 'focusTab'));

		// set a flag that GUI has been build up
		umc.tools.status('setupGui', true);
		this.onGuiDone();
	},

	onGuiDone: function() {
		// event stub
	}
});

