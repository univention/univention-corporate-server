/*
 * Copyright 2011-2012 Univention GmbH
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
/*global define require console window*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/on",
	"dojo/Evented",
	"dojo/Deferred",
	"dojo/cookie",
	"dojo/topic",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/CheckedMenuItem",
	"dijit/MenuSeparator",
	"dijit/form/DropDownButton",
	"dijit/layout/BorderContainer",
	"dijit/layout/TabContainer",
	"umc/tools",
	"umc/dialog",
	"umc/help",
	"umc/about",
	"umc/widgets/CategoryPane",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/i18n!umc/branding,umc/app"
], function(declare, lang, array, win, on, Evented, Deferred, cookie, topic, Menu, MenuItem, CheckedMenuItem, MenuSeparator, DropDownButton, BorderContainer, TabContainer, tools, dialog, help, about, CategoryPane, ContainerWidget, Page, Text, Button, _) {
	var _App = declare([ Evented ], {
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
			tools.status('width', props.width);
			tools.status('displayUsername', tools.isTrue(props.displayUsername));
			// username will be overriden by final authenticated username
			tools.status('username', props.username || cookie('UMCUsername'));
			// password has been given in the query string... in this case we may cache it, as well
			tools.status('password', props.password);

			if (typeof props.module == "string") {
				// a startup module is specified
				on.once(this, 'GuiDone', lang.hitch(this, function() {
					this.openModule(props.module, props.flavor);
					this._tabContainer.layout();

					// put focus into the CategoryPane for scrolling
					/*dijit.focus(this._categoryPane.domNode);
					this.on(_categoryPane, 'show', function() {
						dijit.focus(this._categoryPane.domNode);
					});*/
				}));

				tools.status('overview', tools.isTrue(props.overview));
			}

			if (props.username && props.password && typeof props.username == "string" && typeof props.password == "string") {
				// username and password are given, try to login directly
				dialog.login().then(lang.hitch(this, 'onLogin'));
				return;
			}

			// check whether we still have a possibly valid cookie
			var sessionCookie = cookie('UMCSessionId');
			var usernameCookie = cookie('UMCUsername');
			if (undefined !== sessionCookie && usernameCookie !== undefined &&
				(!tools.status('username') || tools.status('username') == usernameCookie)) {
				// the following conditions need to be given for an automatic login
				// * session and username need to be set via cookie
				// * if a username is given via the query string, it needs to match the
				//   username saved in the cookie
				this.onLogin(cookie('UMCUsername'));
			}
			else {
				dialog.login().then(lang.hitch(this, 'onLogin'));
			}
		},

		onLogin: function(username) {
			// save the username internally and as cookie
			cookie('UMCUsername', username, { expires: 100, path: '/' });
			tools.status('username', username);

			// load required ucr variables
			tools.ucr(['umc/web/feedback/mail', 'umc/web/feedback/description', 'umc/http/session/timeout']).then( function(res) {
				tools._sessionTimeout = parseInt( res['umc/http/session/timeout'] , 10 );

				tools.status('feedbackAddress', res['umc/web/feedback/mail'] || tools.status('feedbackAddress'));
				tools.status('feedbackSubject', encodeURIComponent(res['umc/web/feedback/description']) || tools.status('feedbackSubject'));
			} );

			// start the timer for session checking
			tools.checkSession(true);

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
			//		open modules from other modules without requiring 'umc/app'.
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
			try {
				var params = lang.mixin({
					title: module.name,
					iconClass: tools.getIconClass(module.icon),
					closable: tools.status('overview'),  // closing tabs is only enabled of the overview is visible
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
			} catch (err) {
				console.log('Error initializing module ' + module.id + ':', err);
			}
		},

		focusTab: function(tab) {
			if (array.indexOf(this._tabContainer.getChildren(), tab) >= 0) {
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
			// if only one module exists open it
			if (this._modules.length === 1) {
				this.openModule(this._modules[0].id, this._modules[0].flavor);
			}
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

			tools.umcpCommand('get/modules/list', null, false).then(lang.hitch(this, function(data) {
				// helper function for sorting, sort indeces with priority < 0 to be at the end
				var _cmp = function(x, y) {
					if (y.priority == x.priority) {
						return x._orgIndex - y._orgIndex;
					}
					return y.priority - x.priority;
				};

				// get all categories
				array.forEach(lang.getObject('categories', false, data), lang.hitch(this, function(icat, i) {
					icat._orgIndex = i;  // save the element's original index
					this._categories.push(icat);
				}));
				this._categories.sort(_cmp);

				// register error handler
				var modules = lang.getObject('modules', false, data) || [];
				var ndeps = 0;
				var modulesLoaded = new Deferred();
				var incDeps = function() {
					// helper function
					++ndeps;
					if (ndeps == modules.length) {
						// all modules have been loaded
						modulesLoaded.resolve();
					}
				};
				var errHandle = require.on('error', function(err) {
					// count the loaded dependencies
					// TODO: this error handling is not quite correct
					console.log('### error:', err);
					if (err.message == 'scriptError') {
						incDeps();
					}
				});

				// get all modules
				array.forEach(modules, lang.hitch(this, function(module, i) {
					// try to load the module
					try {
						require(['umc/modules/' + module.id], lang.hitch(this, function(baseClass) {
							// add module config class to internal list of available modules
							this._modules.push(lang.mixin({
								BaseClass: baseClass,
								_orgIndex: i  // save the element's original index
							}, module));
							incDeps();
						}));
					} catch (err) {
						console.log('Error loading module ' + module.id + ':', err);
					}

				}));

				modulesLoaded.then(lang.hitch(this, function() {
					// all modules have been loaded ... unregister error handelr
					errHandle.remove();

					// sort the internal list of modules
					this._modules.sort(_cmp);

					// disable overview if only one module exists
					tools.status('overview', (this._modules.length !== 1) && tools.status('overview'));

					// loading is done
					this.onModulesLoaded();
					this._modulesLoaded = true;
				}));
			}), lang.hitch(this, function() {
				dialog.login().then(lang.hitch(this, 'onLogin'));
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
			if (tools.status('setupGui')) {
				return;
			}

			// set up fundamental layout parts
			var topContainer = new BorderContainer( {
				'class': 'umcTopContainer',
				gutters: false,
				// force a displayed width if specified
				style: tools.status('width') ? 'width:' + tools.status('width') + 'px;' : null
			}).placeAt(win.body());

			// container for all modules tabs
			this._tabContainer = new TabContainer({
				region: 'center',
				'class': 'umcMainTabContainer'
			});
			topContainer.addChild(this._tabContainer);

			if (tools.status('overview')) {
				// the container for all category panes
				// NOTE: We add the icon here in the first tab, otherwise the tab heights
				//	   will not be computed correctly and future tabs will habe display
				//	   problems.
				//     -> This could probably be fixed by calling layout() after adding a new tab!
				var overviewPage = new Page({
					title: _('umcOverviewTabTitle'),
					headerText: _('umcOverviewHeader'),
					iconClass: tools.getIconClass('univention'),
					helpText: _('umcOverviewHelpText')
				});
				this._tabContainer.addChild(overviewPage);

				// get needed UCR variables
				tools.umcpCommand( 'get/ucr', [ 'ssl/validity/host', 'ssl/validity/root', 'ssl/validity/warning', 'update/available', 'update/reboot/required' ] ).then( lang.hitch( this, function( data ) {
					// check validity of SSL certificates
					var hostCert = parseInt( data.result[ 'ssl/validity/host' ], 10 );
					var rootCert = parseInt( data.result[ 'ssl/validity/root' ], 10 );
					var warning = parseInt( data.result[ 'ssl/validity/warning' ], 10 );
					var certExp = rootCert;
					var certType = this._('SSL root certificate');
					if (rootCert >= hostCert) {
						certExp = hostCert;
						certType = this._('SSL host certificate');
					}
					var today = new Date().getTime() / 1000 / 60 / 60 / 24; // now in days
					var days = certExp - today;
					if ( days <= warning ) {
						overviewPage.addNote( this._( 'The %s will expire in %d days and should be renewed!', certType, days ) );
					}

					// check if updates are available
					if ( this.getModule('updater') && tools.isTrue(data.result['update/available']) ) {
						var link = 'href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'updater\')"';
						overviewPage.addNote( _( 'An update for UCS is available. Please visit <a %s>Online Update Module</a> to install the updates.', link ) );
					}

					// check if system reboot is required
					if ( this.getModule('reboot') && tools.isTrue(data.result['update/reboot/required']) ) {
						var link_reboot = 'href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'reboot\')"';
						overviewPage.addNote( _( 'This system has been updated recently. Please visit the <a %s>Reboot Module</a> and reboot this system to finish the update.', link_reboot ) );
					}
				}));

				// add a CategoryPane for each category
				var categories = ContainerWidget({
					scrollable: true
				});
				array.forEach(this.getCategories(), lang.hitch(this, function(icat) {
					// ignore empty categories
					var modules = this.getModules(icat.id);
					if (0 === modules.length) {
						return;
					}

					// create a new category pane for all modules in the given category
					this._categoryPane = new CategoryPane({
						modules: modules,
						title: icat.name,
						open: true //('favorites' == icat.id)
					});

					// register to requests for opening a module
					on(this._categoryPane, 'openModule', lang.hitch(this, 'openModule'));

					// add category pane to overview page
					categories.addChild(this._categoryPane);
				}));
				overviewPage.addChild(categories);
			}

			// the header
			var header = new ContainerWidget({
				'class': 'umcHeader',
				region: 'top'
			});
			topContainer.addChild( header );

			// we need containers aligned to the left and the right
			var headerLeft = new ContainerWidget({
				style: 'float: left'
			});
			header.addChild(headerLeft);
			var headerRight = new ContainerWidget({
				style: 'float: right'
			});
			header.addChild(headerRight);

			// the univention context menu
			var univentionMenu = new Menu({});
			univentionMenu.addChild(new MenuItem({
				label: _('Help'),
				onClick : help
			}));
			if ( this.getModule( 'udm' ) ) {
				require(['umc/modules/udm/LicenseDialog'], function(LicenseDialog) {
					univentionMenu.addChild(new MenuItem({
						label: _('License'),
						onClick : function() {
							var dlg = new LicenseDialog();
							dlg.show();
						}
					}), 2);
				});
			}
			univentionMenu.addChild(new MenuItem({
				label: _('About UMC'),
				onClick : function() {
					tools.umcpCommand( 'get/info' ).then( function( data ) {
						about( data.result );
					} );
				}
			}));
			univentionMenu.addChild(new MenuSeparator({}));
			univentionMenu.addChild(new MenuItem({
				label: _('Univention Website'),
				onClick: function() {
					var w = window.open( 'http://www.univention.de/', 'UMC' );
					w.focus();
				}
			}));
			headerLeft.addChild(new DropDownButton({
				'class': 'umcHeaderButton univentionButton',
				iconClass: 'univentionLogo',
				dropDown: univentionMenu
			}));

			// query domainname and hostname and add this information to the header
			var hostInfo = new Text( {
				templateString: '<span dojoAttachPoint="contentNode">${content}</span>',
				content: '...',
				'class': 'umcHeaderText'
			} );
			headerRight.addChild(hostInfo);
			tools.umcpCommand('get/ucr', [ 'domainname', 'hostname' ]).
				then(lang.hitch(this, function(data) {
					var domainname = data.result.domainname;
					var hostname = data.result.hostname;
					hostInfo.set('content', _('umcHostInfo', {
						domain: domainname,
						host: hostname
					}));

					// save hostname and domainname as status information
					tools.status('domainname', domainname);
					tools.status('hostname', hostname);
				}));

			// the user context menu
			var userMenu = new Menu({});
			userMenu.addChild(new CheckedMenuItem({
				label: _('Tooltips'),
				checked: tools.preferences('tooltips'),
				onClick: function() {
					tools.preferences('tooltips', this.checked);
				}
			}));
			/*userMenu.addChild(new CheckedMenuItem({
				label: _('Confirmations'),
				checked: true,
				checked: tools.preferences('confirm'),
				onClick: function() {
					tools.preferences('confirm', this.checked);
				}
			}));*/
			userMenu.addChild(new CheckedMenuItem({
				label: _('Module help description'),
				checked: tools.preferences('moduleHelpText'),
				onClick: function() {
					tools.preferences('moduleHelpText', this.checked);
				}
			}));
			if (tools.status('displayUsername')) {
				headerRight.addChild(new DropDownButton({
					label: _('umcUserInfo', {
						username: tools.status('username')
					}),
					'class': 'umcHeaderButton',
					dropDown: userMenu
				}));
			}

			// add logout button
			headerRight.addChild(new Button({
				label: '<img src="js/dijit/themes/umc/logout.png">',
				'class': 'umcHeaderButton umcLogoutButton',
				onClick: lang.hitch(this, function() {
					dialog.confirm(_('Do you really want to logout?'), [{
						label: _('Logout'),
						auto: true,
						callback: lang.hitch(this, function() {
							tools.closeSession();
							window.location.reload();
						})
					}, {
						label: _('Cancel'),
						'default': true
					}]);
				})
			}));

			// put everything together
			topContainer.startup();

			// subscribe to requests for opening modules and closing/focusing tabs
			topic.subscribe('/umc/modules/open', lang.hitch(this, 'openModule'));
			topic.subscribe('/umc/tabs/close', lang.hitch(this, 'closeTab'));
			topic.subscribe('/umc/tabs/focus', lang.hitch(this, 'focusTab'));

			// set a flag that GUI has been build up
			tools.status('setupGui', true);
			this.onGuiDone();
		},

		onGuiDone: function() {
			// event stub
		}
	});
	return new _App();
});
