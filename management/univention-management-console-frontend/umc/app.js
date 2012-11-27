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
/*global define require console window getQuery*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/on",
	"dojo/has",
	"dojo/Evented",
	"dojo/Deferred",
	"dojo/promise/all",
	"dojo/cookie",
	"dojo/topic",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dijit/Dialog",
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
	"umc/widgets/ProgressInfo",
	"umc/widgets/GalleryPane",
	"umc/widgets/TitlePane",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/i18n!umc/branding,umc/app",
	"dojo/sniff" // has("ie"), has("ff")
], function(declare, lang, array, win, on, has, Evented, Deferred, all, cookie, topic, Memory, Observable, Dialog, Menu, MenuItem, CheckedMenuItem, MenuSeparator, DropDownButton, BorderContainer, TabContainer, tools, dialog, help, about, ProgressInfo, GalleryPane, TitlePane, ContainerWidget, Page, Text, Button, _) {
	// cache UCR variables
	var _ucr = {};
	var _userPreferences = {};

	// helper function for sorting, sort indeces with priority < 0 to be at the end
	var _cmp = function(x, y) {
		if (y.priority == x.priority) {
			return x._orgIndex - y._orgIndex;
		}
		return y.priority - x.priority;
	};

	// helper function that sorts using the favorites position
	var _cmpFavorites = function(x, y) {
		return x._favoritePos - y._favoritePos;
	};

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

					// put focus into the GalleryPane for scrolling
					/*dijit.focus(this._categoryPane.domNode);
					this.on(_categoryPane, 'show', function() {
						dijit.focus(this._categoryPane.domNode);
					});*/
				}));

			}
			tools.status('overview', tools.isTrue(props.overview));

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

			// start the timer for session checking
			tools.checkSession(true);

			// setup static GUI part
			this.setupStaticGui();

			// load the modules
			this.loadModules();
		},

		_tabContainer: null,
		_overviewPage: null,
		_univentionMenu: null,
		_hostInfo: null,
		_categoriesContainer: null,
		_favoritesEnabled: true,

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
				tools.checkReloadRequired();
			} catch (err) {
				console.log('Error initializing module ' + module.id + ':', err);
				tools.checkReloadRequired();
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
			// load required ucr variables
			tools.status('sessionTimeout', parseInt( _ucr['umc/http/session/timeout'] , 10 ) || tools.status('sessionTimeout'));
			tools.status('feedbackAddress', _ucr['umc/web/feedback/mail'] || tools.status('feedbackAddress'));
			tools.status('feedbackSubject', _ucr['umc/web/feedback/description'] || tools.status('feedbackSubject'));

			// setup the dynamic part of the GUI
			this.setupGui();

			// if only one module exists open it
			var modules = this._moduleStore.query();
			if (modules.length === 1 && !getQuery('module')) {
				this.openModule(modules[0].id, modules[0].flavor);
			}
		},

		_moduleStore: null,
		_categories: [{
			// default category for favorites
			id: '$favorites$',
			name: _('Favorites'),
			priority: 100
		}],
		_modulesLoaded: false,
		loadModules: function() {
			// make sure that we don't load the modules twice
			if (this._modulesLoaded) {
				this.onModulesLoaded();
				return;
			}

			// load some important UCR variables
			var ucrDeferred = tools.ucr([
				'domainname',
				'hostname',
				'umc/web/feedback/mail',
				'umc/web/feedback/description',
				'umc/web/favorites/default',
				'umc/http/session/timeout',
				'ssl/validity/host',
				'ssl/validity/root',
				'ssl/validity/warning',
				'update/available',
				'update/reboot/required'
			]).then(lang.hitch(this, function(res) {
				// save the ucr variables in a local variable
				lang.mixin(_ucr, res);
			}));

			// load user settings
			var userPreferencesDefered = tools.getUserPreferences().then(lang.hitch(this, function(prefs) {
				lang.mixin(_userPreferences, prefs);
				this._favoritesEnabled = true;
			}), lang.hitch(this, function() {
				// user preferences disabled
				this._favoritesEnabled = false;
			}));

			// prompt a dialog showing the progress of loading modules
			var progressInfo = new ProgressInfo({});
			var progressDialog = new Dialog({
				content: progressInfo
			});
			progressInfo.updateTitle(_('Loading modules'));
			progressInfo.updateInfo('&nbsp;');
			progressDialog.show();

			// load the modules dynamically
			var modules = [];
			var modulesDeferred = tools.umcpCommand('get/modules/list', null, false).then(lang.hitch(this, function(data) {
				// update progress
				var _modules = lang.getObject('modules', false, data) || [];
				progressInfo.maximum = _modules.length;
				progressInfo.update(0);

				// get all categories
				array.forEach(lang.getObject('categories', false, data), lang.hitch(this, function(icat, i) {
					icat._orgIndex = i;  // save the element's original index
					this._categories.push(icat);
				}));
				this._categories.sort(_cmp);

				// register error handler
				var ndeps = 0;
				var modulesLoaded = new Deferred();
				var incDeps = function(moduleName) {
					// helper function
					++ndeps;
					progressInfo.update(ndeps, moduleName ? _('Loaded module %s', moduleName) : '&nbsp;');
					if (ndeps >= _modules.length) {
						// all modules have been loaded
						modulesLoaded.resolve();
						progressDialog.hide().then(function() {
							progressInfo.destroyRecursive();
						});
					}
				};
				var errHandle = require.on('error', function(err) {
					// count the loaded dependencies
					// TODO: revise this error handling
					if (err.message == 'scriptError') {
						incDeps();
					}
				});

				// get all modules
				array.forEach(_modules, lang.hitch(this, function(module, i) {
					// try to load the module
					try {
						require(['umc/modules/' + module.id], lang.hitch(this, function(baseClass) {
							if (typeof baseClass == "function" && tools.inheritsFrom(baseClass.prototype, 'umc.widgets._ModuleMixin')) {
								// add module config class to internal list of available modules
								modules.push(lang.mixin({
									BaseClass: baseClass,
									_orgIndex: i  // save the element's original index
								}, module));
							}
							incDeps(module.name);
						}));
					} catch (err) {
						console.log('Error loading module ' + module.id + ':', err);
					}

					// return deferred that fires when all dependencies are loaded
				}));

				// resolve the deferred object directly if there are no modules available
				if (!_modules.length) {
					incDeps();
				}

				return modulesLoaded;
			})).then(lang.hitch(this, function() {
				// sort the internal list of modules
				modules.sort(_cmp);

				// create a store for the module items
				array.forEach(modules, function(item) {
					// we need a uniqe ID for the store
					item.$id$ = item.id + ':' + item.flavor;
				});
				this._moduleStore = new Observable(new Memory({
					data: modules,
					idProperty: '$id$'
				}));

				// make sure that we do not overwrite an explicitely stated value of 'overview'
				if (getQuery('overview') === undefined) {
					// disable overview if only one module exists
					tools.status('overview', modules.length !== 1 && tools.status('overview'));
				}
			}));

			// wait for modules, the UCR variables, and user preferences to load
			all([modulesDeferred, ucrDeferred, userPreferencesDefered]).then(lang.hitch(this, function() {
				// loading is done
				this.onModulesLoaded();
				this._modulesLoaded = true;
			}), lang.hitch(this, function() {
				// something went wrong... try to login again
				progressDialog.hide().then(function() {
					progressInfo.destroyRecursive();
				});
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
			var query = {};
			if (category) {
				query.categories = {
					test: function(categories) {
						return array.indexOf(categories, category) >= 0;
					}
				};
			}
			return this._moduleStore.query(query, { sort: _cmp } );
		},

		getModule: function(/*String?*/ id, /*String?*/ flavor, /*String?*/ category) {
			// summary:
			//		Get the module object for a given module ID.
			//		The returned object has the following properties:
			//		{ BaseClass, id, description, category, flavor }.
			// id:
			//		Module ID as string.
			// flavor:
			//		The module flavor as string.
			// category:
			//		Restricts the search only to the given category.

			var query = {
				id: id,
				flavor: flavor || /.*/
			};
			if (category) {
				query.categories = {
					test: function(categories) {
						return array.indexOf(categories, category) >= 0;
					}
				};
			}
			var res = this._moduleStore.query(query);
			if (res.length) {
				return res[0];
			}
			return undefined;
		},

		getCategories: function() {
			// summary:
			//		Get all categories as an array. Each entry has the following properties:
			//		{ id, description }.
			return this._categories; // Object[]
		},

		getCategory: function(/*String*/ id) {
			// summary:
			//		Get all categories as an array. Each entry has the following properties:
			//		{ id, description }.
			var res = array.filter(this._categories, function(icat) {
				return icat.id == id;
			});
			if (res.length <= 0) {
				return undefined; // undefined
			}
			return res[0];
		},

		_favorites_for_not_existing_modules: {},
		_saveFavorites: function() {
			if (!tools.status('setupGui')) {
				return;
			}

			// get all favorite modules
			var modules = this._moduleStore.query({
				categories: {
					test: function(categories) {
						return array.indexOf(categories, '$favorites$') >= 0;
					}
				}
//			}, {
//				sort: _cmpFavorites
			});
			tools.forIn(this._favorites_for_not_existing_modules, function(ikey, ivalue) {
				modules.push(ivalue);
			});
			modules.sort(_cmpFavorites);

			// save favorites as a comma separated list
			var favoritesStr = array.map(modules, function(imod) {
				return imod.flavor ? imod.id + ':' + imod.flavor : imod.id;
			}).join(',');

			// store updated favorites
			tools.setUserPreference({favorites: favoritesStr});
		},

		_favoriteIdx: 0,
		addFavoriteModule: function(/*String*/ id, /*String?*/ flavor) {
			if (this.getModule(id, flavor, '$favorites$')) {
				// module has already been added to the favorites
				return;
			}
			var mod = this.getModule(id, flavor);
			if (!mod) {
				// module does not exist (on this server), we add a dummy module
				var $id$ = id + ':' + flavor;
				if (!this._favorites_for_not_existing_modules[$id$]) {
					this._favorites_for_not_existing_modules[$id$] = {
						id: id,
						flavor: flavor,
						_favoritePos: this._favoriteIdx++
					};
				}
				return;
			}

			// add a module clone for favorite category
			mod.categories.push('$favorites$');
			mod._favoritePos = this._favoriteIdx;
			this._favoriteIdx++;
			this._moduleStore.put(mod);

			// save settings
			this._saveFavorites();
		},

		removeFavoriteModule: function(/*String*/ id, /*String?*/ flavor) {
			var mod = this.getModule(id, flavor, '$favorites$');
			if (!mod) {
				// module is not part of the favorites
				delete this._favorites_for_not_existing_modules[id + ':' + flavor];
				return;
			}

			// remove favorites category
			var idx = array.indexOf(mod.categories, '$favorites$');
			if (idx >= 0) {
				mod.categories.splice(idx, 1);
			}
			this._moduleStore.put(mod);

			// save settings
			this._saveFavorites();
		},

		setupGui: function() {
			// make sure that we have not build the GUI before
			if (tools.status('setupGui')) {
				return;
			}

			// try to insert license dialog
			if ( this.getModule( 'udm' ) ) {
				require(['umc/modules/udm/LicenseDialog'], lang.hitch(this, function(LicenseDialog) {
					this._univentionMenu.addChild(new MenuItem({
						label: _('License'),
						onClick : function() {
							var dlg = new LicenseDialog();
							dlg.show();
						}
					}), 2);
				}));
			}

			// update the host information in the header
			this._hostInfo.set('content', _('umcHostInfo', {
				domain: _ucr.domainname,
				host: _ucr.hostname
			}));

			// save hostname and domainname as status information
			tools.status('domainname', _ucr.domainname);
			tools.status('hostname', _ucr.hostname);

			if (tools.status('overview')) {
				// the container for all category panes
				// NOTE: We add the icon here in the first tab, otherwise the tab heights
				//	   will not be computed correctly and future tabs will habe display
				//	   problems.
				//     -> This could probably be fixed by calling layout() after adding a new tab!
				this._overviewPage = new Page({
					title: _('umcOverviewTabTitle'),
					headerText: _('umcOverviewHeader'),
					iconClass: tools.getIconClass('univention'),
					helpText: _('umcOverviewHelpText')
				});

				// prepare the widget displaying all categories
				this._categoriesContainer = new ContainerWidget({
					scrollable: true
				});
				this._overviewPage.addChild(this._categoriesContainer);
				this._tabContainer.addChild(this._overviewPage);

				// check validity of SSL certificates
				var hostCert = parseInt( _ucr[ 'ssl/validity/host' ], 10 );
				var rootCert = parseInt( _ucr[ 'ssl/validity/root' ], 10 );
				var warning = parseInt( _ucr[ 'ssl/validity/warning' ], 10 );
				var certExp = rootCert;
				var certType = _('SSL root certificate');
				if (rootCert >= hostCert) {
					certExp = hostCert;
					certType = _('SSL host certificate');
				}
				var today = new Date().getTime() / 1000 / 60 / 60 / 24; // now in days
				var days = certExp - today;
				if ( days <= warning ) {
					this._overviewPage.addNote( _( 'The %s will expire in %d days and should be renewed!', certType, days ) );
				}

				// check if updates are available
				if ( this.getModule('updater') && tools.isTrue(_ucr['update/available']) ) {
					var link = 'href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'updater\')"';
					this._overviewPage.addNote( _( 'An update for UCS is available. Please visit <a %s>Online Update Module</a> to install the updates.', link ) );
				}
				if (has('ie') < 9 || has('ff') < 4) {
					// supported browsers are FF 3.6 and IE 8
					// they should work with UMC. albeit, they are
					// VERY slow and escpecially IE 8 may take minutes (!)
					// to load a heavy UDM object (on a slow computer at least).
					// IE 8 is also known to cause timeouts when under heavy load
					// (presumably because of many async requests to the server
					// during UDM-Form loading)
					this._overviewPage.addNote( _( 'Your Browser is outdated and should be updated. You may continue to use Univention Management Console but you may experience performance issues and other problems.' ) );
				}

				// check if system reboot is required
				if ( this.getModule('reboot') && tools.isTrue(_ucr['update/reboot/required']) ) {
					var link_reboot = 'href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'reboot\')"';
					this._overviewPage.addNote( _( 'This system has been updated recently. Please visit the <a %s>Reboot Module</a> and reboot this system to finish the update.', link_reboot ) );
				}

				// helper function for rendering a category
				var _renderCategory = function(icat) {
					// ignore empty categories
					var modules = this.getModules(icat.id);
					if (0 === modules.length) {
						return;
					}

					// create a new category for all modules in the given category
					var titlepane = new TitlePane({
						title: icat.name,
						open: true //('favorites' == icat.id)
					});
					var gallery = new GalleryPane({
						baseClass: !this._favoritesEnabled ? null : (icat.id == '$favorites$') ? 'umcOverviewFavorites' : 'umcOverviewCategory',
						store: this._moduleStore,
						categoriesDisplayed: false,
						getStatusIconClass: function(item) {
							if (icat.id != '$favorites$' && array.indexOf(item.categories, '$favorites$') >= 0) {
								return tools.getIconClass('star', 24);
							}
							return '';
						},
						getStatusIconTooltip: lang.hitch(this, function(item) {
							if (this._favoritesEnabled) {
								if (icat.id == '$favorites$' || array.indexOf(item.categories, '$favorites$') >= 0) {
									return _('Remove from favorites');
								} else {
									return _('Add to favorites');
								}
							}
						}),
						query: {
							categories: {
								test: function(categories) {
									return array.indexOf(categories, icat.id) >= 0;
								}
							}
						},
						queryOptions: {
							sort: icat.id == '$favorites$' ? _cmpFavorites : _cmp
						}
					});
					titlepane.addChild(gallery);

					if (this._favoritesEnabled) {
						// register to requests for adding a module to the favorites
						gallery.on('.umcGalleryStatusIcon:click', lang.hitch(this, function(evt) {
							// prevent event bubbling
							evt.stopImmediatePropagation();

							var item = gallery.row(evt).data;
							if (array.indexOf(item.categories, '$favorites$') >= 0) {
								// for the favorite category, remove the moduel from the favorites
								this.removeFavoriteModule(item.id, item.flavor);
							}
							else {
								// for any other category, add the module to the favorites
								this.addFavoriteModule(item.id, item.flavor);
							}
						}));
					}

					// register to requests for opening a module
					gallery.on('.umcGalleryItem:click', lang.hitch(this, function(evt) {
						var item = gallery.row(evt).data;
						this.openModule(gallery.row(evt).data);
					}));

					// add category to overview page
					this._categoriesContainer.addChild(titlepane);
				};

				if (this._moduleStore.query().length > 4) {
					// handle favorites category... query user preferences and
					// use as fallback the corresponding UCR variable...
					var favoritesStr = _userPreferences.favorites || _ucr['umc/web/favorites/default'] || '';
					array.forEach(lang.trim(favoritesStr).split(/\s*,\s*/), function(ientry) {
						this.addFavoriteModule.apply(this, ientry.split(':'));
					}, this);
				}
				else {
					// disable favorites for modules <= 4 completely
					this._favoritesEnabled = false;
				}

				// render all standard categories
				array.forEach(this.getCategories(), lang.hitch(this, _renderCategory));
			}

			// show a message in case no module is available
			if (!this._moduleStore.query().length) {
				dialog.alert(_('There is no module available for the authenticated user %s.', tools.status('username')));
			}

			// set a flag that GUI has been build up
			tools.status('setupGui', true);
			this.onGuiDone();
		},

		_setupStaticGui: false,

		setupStaticGui: function() {
			// setup everythin that can be set up statically

			// make sure that we have not build the GUI before
			if (this._setupStaticGui) {
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
			this._univentionMenu = new Menu({});
			this._univentionMenu.addChild(new MenuItem({
				label: _('Help'),
				onClick : help
			}));
			this._univentionMenu.addChild(new MenuItem({
				label: _('About UMC'),
				onClick : function() {
					tools.umcpCommand( 'get/info' ).then( function( data ) {
						about( data.result );
					} );
				}
			}));
			this._univentionMenu.addChild(new MenuSeparator({}));
			this._univentionMenu.addChild(new MenuItem({
				label: _('Univention Website'),
				onClick: function() {
					var w = window.open( 'http://www.univention.de/', 'UMC' );
					w.focus();
				}
			}));
			headerLeft.addChild(new DropDownButton({
				'class': 'umcHeaderButton univentionButton',
				iconClass: 'univentionLogo',
				dropDown: this._univentionMenu
			}));

			// query domainname and hostname and add this information to the header
			this._hostInfo = new Text( {
				templateString: '<span dojoAttachPoint="contentNode">${content}</span>',
				content: '...',
				'class': 'umcHeaderText'
			} );
			headerRight.addChild(this._hostInfo);

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

			this._setupStaticGui = true;
		},

		onGuiDone: function() {
			// event stub
		}
	});
	return new _App();
});
