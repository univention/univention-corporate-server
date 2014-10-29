/*
 * Copyright 2011-2014 Univention GmbH
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
/*global umc,define,require,console,window,getQuery,setTimeout*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/window",
	"dojo/on",
	"dojo/aspect",
	"dojo/has",
	"dojo/Evented",
	"dojo/Deferred",
	"dojo/when",
	"dojo/promise/all",
	"dojo/cookie",
	"dojo/topic",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dojo/dom",
	"dojo/dom-style",
	"dojo/dom-attr",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/dom-construct",
	"dojo/date/locale",
	"dojox/html/styles",
	"dojox/html/entities",
	"dojox/gfx",
	"dijit/registry",
	"umc/tools",
	"umc/dialog",
	"umc/store",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/PopupMenuItem",
	"dijit/MenuSeparator",
	"dijit/Tooltip",
	"dijit/form/DropDownButton",
	"dijit/layout/StackContainer",
	"umc/widgets/TabController",
	"umc/widgets/LiveSearchSidebar",
	"umc/widgets/GalleryPane",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"umc/widgets/Button",
	"umc/widgets/Text",
	"umc/app/CategoryButton",
	"umc/i18n!",
	"dojo/sniff" // has("ie"), has("ff")
], function(declare, lang, kernel, array, baseWin, win, on, aspect, has,
		Evented, Deferred, when, all, cookie, topic, Memory, Observable,
		dom, style, domAttr, domClass, domGeometry, domConstruct, locale, styles, entities, gfx, registry, tools, dialog, store,
		Menu, MenuItem, PopupMenuItem, MenuSeparator, Tooltip, DropDownButton, StackContainer,
		TabController, LiveSearchSidebar, GalleryPane, ContainerWidget, Page, Button, Text, CategoryButton, _
) {
	// cache UCR variables
	var _ucr = {};
	var _favoritesDisabled = false;

	var _getLang = function() {
		return kernel.locale.split('-')[0];
	};

	var _hasFFPULicense = function() {
		return _ucr['license/base'] == 'Free for personal use edition';
	};

	// helper function for sorting, sort indeces with priority < 0 to be at the end
	var _cmpPriority = function(x, y) {
		if (y.priority == x.priority) {
			return x._orgIndex - y._orgIndex;
		}
		return y.priority - x.priority;
	};

	// "short" cut (well at least more verbose) for checking for favorite module
	var isFavorite = function(mod) {
		return array.indexOf(mod.categories, '_favorites_') >= 0;
	};

	var _OverviewPane = declare([GalleryPane], {
//		categories: null,

		constructor: function(props) {
			lang.mixin(this, props);
		},

		postMixInProperties: function() {
			this.queryOptions = {
				sort: [{
					attribute: 'categoryPriority',
					descending: true
				}, {
					attribute: 'category',
					descending: false
				}, {
					attribute: 'priority',
					descending: true
				}, {
					attribute: 'name',
					descending: false
				}]
			};
		},

		getIconClass: function(item) {
			if (item.icon) {
				var icon;
				if (/\.svg$/.test(item.icon)) {
					icon = item.icon.replace(/\.svg$/, '');
				} else {
					// for backwards compatibility we need to support png
					icon = lang.replace('{icon}.png', item);
				}
				return tools.getIconClass(icon, 50);
			}
			return '';
		},

//		_onNotification: function() {
//			this._updateCategoryHeaderVisiblity(this._lastCollection);
//		},

//		_getCategory: function(categoryID) {
//			var categories = array.filter(this.categories, function(icat) {
//				return icat.id == categoryID;
//			});
//			if (!categories.length) {
//				return null;
//			}
//			return categories[0];
//		},

		_createFavoriteIcon: function(categoryColor, parentNode) {
			var _createIcon = function(nodeClass, color) {
				var node = domConstruct.create('div', { 'class': nodeClass }, parentNode);
				var surface = gfx.createSurface(node, 10, 10);
				surface.createPolyline([
					{x: 0, y: 0},
					{x: 0, y: 10},
					{x: 5, y: 5.6},
					{x: 10, y: 10},
					{x: 10, y: 0}
				]).setFill(color);
			};

			_createIcon('umcFavoriteIconInverted', 'white');
			_createIcon('umcFavoriteIconDefault', categoryColor);
		},

		renderRow: function(item, options) {
			var div = this.inherited(arguments);
			var category = item.category;
			if (category === '_favorites_' && item.categories.length > 1) {
				category = array.filter(item.categories, function(cat) { return cat != '_favorites_'; })[0];
			}
			var className = lang.replace('umcGalleryCategory-{0}', [category]);
			domClass.add(div.firstElementChild, className);
			if (isFavorite(item)) {
				var cat = require('umc/app').getCategory(category);
				var styleStr = '';
				if (cat) {
					styleStr += lang.replace('background-color: {0};', [cat.color]);
				}
				//domConstruct.create('div', {'class': 'umcGalleryCategoryFavorite', style: styleStr}, div.firstElementChild);
				this._createFavoriteIcon(cat.color, div.firstElementChild);
			}
			return div;
		},

		getItemDescription: function(item) {
			return item.description;
		},

		updateQuery: function(searchPattern, searchQuery, category) {
			var query = function(obj) {
				// sub conditions
				var allCategories = !category;
				var matchesPattern = !searchPattern ||
					// for a given pattern, ignore 'pseudo' entries in _favorites_ category
					(searchQuery.test(null, obj) && obj.category != '_favorites_');
				var matchesCategory = true;
				if (!allCategories) {
					matchesCategory = obj.category == category.id;
				}
				else if (obj.category == '_favorites_') {
					// don't show duplicated modules
					matchesCategory = false;
				}

				// match separators OR modules with a valid class
				return matchesPattern && matchesCategory;
			};

			// set query
			this.set('query', query);
		}
	});

	var _ModuleStore = declare([Memory], {
		data: null,
		modules: null,

		categories: null,

		favoritesDisabled: false,

		idProperty: '$id$',

		constructor: function(modules, categories) {
			this.categories = this._createCategoryList(categories);
			this.setData(this._createModuleList(modules));
			this._pruneEmptyCategories();
		},

		_createModuleList: function(_modules) {
			_modules = _modules.sort(_cmpPriority);
			var modules = [];
			array.forEach(_modules, function(imod) {
				array.forEach(imod.categories || [], function(icat) {
					modules.push(this._createModuleItem(imod, icat));
				}, this);
			}, this);
			return modules;
		},

		_createModuleItem: function(_item, categoryID) {
			// we need a uniqe ID for the store
			var item = lang.mixin({
				categories: []
			}, _item);
			item.$id$ = item.id + ':' + item.flavor;

			if (categoryID) {
				item.$id$ += '#' + categoryID;
				item.category = '' + categoryID;
				item.categoryPriority = lang.getObject('priority', false, this.getCategory(categoryID)) || 0;
			}
			else {
				item.category = '';
				item.categoryPriority = 0;
			}
			return item;
		},

		_createCategoryList: function(_categories) {
			var categories = array.map(_categories, function(icat, i) {
				return lang.mixin(icat, {
					_orgIndex: i,  // save the element's original index
					label: icat.name
				});
			});
			return categories.sort(_cmpPriority);
		},

		_pruneEmptyCategories: function() {
			var nonEmptyCategories = {'_favorites_': true};
			this.query().forEach(function(imod) {
				array.forEach(imod.categories, function(icat) {
					nonEmptyCategories[icat] = true;
				});
			});
			var categories = array.filter(this.categories, function(icat) {
				return nonEmptyCategories[icat.id] === true;
			});
			this.categories = categories;
		},

		setFavoritesString: function(favoritesStr) {
			favoritesStr = favoritesStr || '';
			array.forEach(lang.trim(favoritesStr).split(/\s*,\s*/), function(ientry) {
				this.addFavoriteModule.apply(this, ientry.split(':'));
			}, this);
		},

		_saveFavorites: function() {
			if (!tools.status('setupGui')) {
				return;
			}

			// get all favorite modules
			var modules = this.query({
				category: '_favorites_'
			});

			// save favorites as a comma separated list
			var favoritesStr = array.map(modules, function(imod) {
				return imod.flavor ? imod.id + ':' + imod.flavor : imod.id;
			}).join(',');

			// store updated favorites
			tools.setUserPreference({favorites: favoritesStr});/*.otherwise(function() {
				_favoritesDisabled = true;
			});*/
		},

		getCategories: function() {
			return this.categories; // Object[]
		},

		getCategory: function(/*String*/ id) {
			var res = array.filter(this.categories, function(icat) {
				return icat.id == id;
			});
			if (res.length <= 0) {
				return undefined; // undefined
			}
			return res[0];
		},

		getModules: function(/*String?*/ category) {
			var query = {};
			if (category) {
				query.categories = {
					test: function(categories) {
						return array.indexOf(categories, category) >= 0;
					}
				};
			}
			return this.query(query, {
				sort: _cmpPriority
			});
		},

		getModule: function(/*String?*/ id, /*String?*/ flavor, /*String?*/ category) {
			var query = {
				id: id,
				flavor: flavor || /.*/,
				// by default, match categories != favorites category
				category: category || /^((?!_favorites_).)*$/
			};
			var res = this.query(query);
			if (res.length) {
				return res[0];
			}
			return undefined;
		},

		addFavoriteModule: function(/*String*/ id, /*String?*/ flavor) {
			var favoriteModule = this.getModule(id, flavor, '_favorites_');
			if (favoriteModule) {
				// module has already been added to the favorites
				return;
			}
			var _mod = this.getModule(id, flavor);
			if (_mod) {
				// add favorite to categories
				_mod.categories = _mod.categories.concat(['_favorites_']);
				this.put(_mod);
			}
			else {
				// module does not exist (on this server), we add a dummy module
				// (this is important when installing a new app which is automatically
				// added to the favorites)
				_mod = {
					id: id,
					flavor: flavor,
					name: id
				};
			}

			// add a module clone for favorite category
			var mod = this._createModuleItem(_mod, '_favorites_');
			this.add(mod);

			// save settings
			this._saveFavorites();
		},

		removeFavoriteModule: function(/*String*/ id, /*String?*/ flavor) {
			// remove favorite module
			var favoriteModule = this.getModule(id, flavor, '_favorites_');
			if (favoriteModule) {
				this.remove(favoriteModule.$id$);
			}

			// remove favorites from categories
			var mod = this.getModule(id, flavor);
			if (mod && isFavorite(mod)) {
				mod.categories = array.filter(mod.categories, function(cat) { return cat !== '_favorites_'; });
				this.put(mod);
			}

			// save settings
			this._saveFavorites();
		}
	});

	topic.subscribe('/umc/started', function() {

		var checkCertificateValidity = function() {
			var hostCert = parseInt(_ucr['ssl/validity/host'], 10);
			var rootCert = parseInt(_ucr['ssl/validity/root'], 10);
			var warning = parseInt(_ucr['ssl/validity/warning'], 10);
			var certExp = rootCert;
			var certType = _('SSL root certificate');
			if (rootCert >= hostCert) {
				certExp = hostCert;
				certType = _('SSL host certificate');
			}
			var today = new Date().getTime() / 1000 / 60 / 60 / 24; // now in days
			var days = certExp - today;
			if (days <= warning) {
				dialog.warn(_('The %s will expire in %d days and should be renewed!', certType, days));
			}
		};

		var checkBrowser = function() {
			if (has('ie') < 9 || has('ff') < 24) {
				// supported browsers are Chrome >= 33, FF >= 24, IE >=9 and Safari >= 7
				// they should work with UMC. albeit, they are
				// VERY slow and escpecially IE 8 may take minutes (!)
				// to load a heavy UDM object (on a slow computer at least).
				// IE 8 is also known to cause timeouts when under heavy load
				// (presumably because of many async requests to the server
				// during UDM-Form loading)
				dialog.warn(_('Your Browser is outdated and should be updated. You may continue to use Univention Management Console but you may experience performance issues and other problems.'));
			}
		};

		var checkShowStartupDialog = function() {
			var isUserAdmin = tools.status('username').toLowerCase() == 'administrator';
			var isUCRVariableEmpty = !Boolean(_ucr['umc/web/startupdialog']);
			var showStartupDialog = tools.isTrue(_ucr['umc/web/startupdialog']);
			var isDCMaster = _ucr['server/role'] == 'domaincontroller_master';
			if (!isDCMaster || !((isUCRVariableEmpty && _hasFFPULicense() && isUserAdmin) || (showStartupDialog && isUserAdmin))) {
				return;
			}

			require(["umc/app/StartupDialog"], lang.hitch(this, function(StartupDialog) {
				var startupDialog = new StartupDialog({});
				startupDialog.on('hide', function() {
					// dialog is being closed
					// set the UCR variable to false to prevent any further popup
					var ucrStore = store('key', 'ucr');
					ucrStore.put({
						key: 'umc/web/startupdialog',
						value: 'false'
					});
					startupDialog.destroyRecursive();
				});
			}));
		};

		// run several checks
		checkCertificateValidity();
		checkBrowser();
		checkShowStartupDialog();
	});

	var UmcHeader = declare([ContainerWidget], {

		_headerLeft: null,
		_headerRight: null,
		_hostInfo: null,
		_hostMenu: null,
		_menuMap: null,

		setupGui: function() {
			// show the menu bar
			style.set(this._headerRight.domNode, 'display', 'block');
			this.setupHeader();
			this.setupMenus();
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._headerLeft = new ContainerWidget({
				'class': 'umcHeaderLeft col-xxs-12 col-xs-4'
			});
			this.addChild(this._headerLeft);

			this._headerRight = new ContainerWidget({
				'class': 'umcHeaderRight col-xxs-12 col-xs-8'
			});
			this.addChild(this._headerRight);
		},

		setupHeader: function() {
			this._menuMap = {};
			if (tools.status('overview')) {
				// the host info and menu
				this._hostMenu = new Menu({});
				this._hostInfo = new DropDownButton({
					id: 'umcMenuHost',
					label:  _('<b>Host</b> ') + tools.status('fqdn'),
					disabled: true,
					dropDown: this._hostMenu
				});
				this._headerRight.addChild(this._hostInfo);

				// display the username
				this._usernameButton = new DropDownButton({
					id: 'umcMenuUsername',
					'class': 'umcHeaderText',
					label: _('umcUserInfo', {
						username: tools.status('username')
					}),
					dropDown: new Menu({})
				});
				this._headerRight.addChild(this._usernameButton);

				array.forEach([this._hostInfo, this._usernameButton], lang.hitch(this, function(menu) {
					this._menuMap[menu.id] = menu.dropDown;
				}));

				// the settings context menu
				this.addMenuEntry(new PopupMenuItem({
					$parentMenu$: 'umcMenuUsername',
					$priority$: 60,
					label: _('Settings'),
					id: 'umcMenuSettings',
					popup: new Menu({})
				}));

				// the help context menu
				this.addMenuEntry(new PopupMenuItem({
					$parentMenu$: 'umcMenuUsername',
					$priority$: 50,
					label: _('Help'),
					id: 'umcMenuHelp',
					popup: new Menu({})
				}));

				// the logout button
				this.addMenuEntry(new MenuItem({
					$parentMenu$: 'umcMenuUsername',
					$priority$: -1,
					id: 'umcMenuLogout',
					label: _('Logout'),
					onClick: function() { require('umc/app').relogin(); }
				}));
			}

			if (tools.status('overview') && !tools.status('singleModule')) {
				this.setupSearchField();
			}
		},

		addMenuEntry: function(item) {
			if (tools.status('overview')) {
				var menu = this._menuMap[item.$parentMenu$ || 'umcMenuUsername'];
				if (item.isInstanceOf(Menu)) {
					this._menuMap[item.id] = item;
				} else if (item.isInstanceOf(PopupMenuItem)) {
					this._menuMap[item.id] = item.popup;
				} else if (item.isInstanceOf(DropDownButton)) {
					this._menuMap[item.id] = item.dropDown;
				}
				var position = menu.getChildren().length;
				array.forEach(menu.getChildren().reverse(), function(child, pos) {
					if ((child.$priority$ || 0)	<= (menu.$priority$ || 0)) {
						position = pos;
					}
				}, this);
				menu.addChild(item, position);
			}
		},

		setupSearchField: function() {
			// add an empty element to force a line break
			this._headerRight.addChild(new Text({
				'class': 'clearfix'
			}));

			// enforce same width as username button
			var usernameButtonPos = domGeometry.position(this._usernameButton.domNode);
			this._searchSidebar = new LiveSearchSidebar({
				searchLabel: _('Module search'),
				style: lang.replace('width: {w}px', usernameButtonPos)
			});
			this._headerRight.addChild(this._searchSidebar);
		},

		setupMenus: function() {
			this._setupHelpMenu();
			this._setupHostInfoMenu();
		},

		_setupHelpMenu: function() {
			this.addMenuEntry(new MenuItem({
				$parentMenu$: 'umcMenuHelp',
				label: _('Help'),
				onClick : lang.hitch(this, '_showHelpDialog')
			}));

			this.addMenuEntry(new MenuItem({
				$parentMenu$: 'umcMenuHelp',
				label: _('Feedback'),
				onClick : lang.hitch(this, '_showFeedbackPage')
			}));

			this._insertPiwikMenuItem();

			this.addMenuEntry(new MenuItem({
				$parentMenu$: 'umcMenuHelp',
				label: _('About UMC'),
				onClick : lang.hitch(this, '_showAboutDialog')
			}));

			this.addMenuEntry(new MenuSeparator({
				$parentMenu$: 'umcMenuHelp'
			}));

			this.addMenuEntry(new MenuItem({
				$parentMenu$: 'umcMenuHelp',
				label: _('UCS start site'),
				onClick: function() {
					topic.publish('/umc/actions', 'menu-help', 'ucs-start-site');
					var w = window.open('/ucs-overview?lang=' + kernel.locale, 'ucs-start-site');
					w.focus();
				}
			}));

			this.addMenuEntry(new MenuItem({
				$parentMenu$: 'umcMenuHelp',
				label: _('Univention Website'),
				onClick: function() {
					topic.publish('/umc/actions', 'menu-help', 'website');
					var w = window.open(_('umcUniventionUrl'), 'univention');
					w.focus();
				}
			}));
		},

		_insertPiwikMenuItem: function() {
			var isUserAdmin = tools.status('username').toLowerCase() == 'administrator';
			if (!(_hasFFPULicense() && isUserAdmin)) {
				return;
			}
			this.addMenuEntry(new MenuItem({
				$parentMenu$: 'umcMenuHelp',
				label: _('Usage statistics'),
				onClick: lang.hitch(this, '_showPiwikDialog')
			}));
		},

		_showPiwikDialog: function() {
			topic.publish('/umc/actions', 'menu-help', 'piwik');
			dialog.templateDialog('umc/app', 'feedback.' + _getLang()  + '.html', {
				path: require.toUrl('umc/app'),
				hardwareStatisticsCheckboxDisplay: 'none',
				version: tools.status('ucsVersion').split('-')[0]
			}, _('Usage statistics'), _('Close'));
		},

		_setupHostInfoMenu: function() {
			if (!this._hostInfo) {
				return;
			}
			// update the host information in the header
			var fqdn = tools.status('fqdn');
			tools.umcpCommand('get/hosts/list').then(lang.hitch(this, function(data) {
				var empty = data.result.length <= 1;
				empty = empty || data.result.length >= (parseInt(_ucr['umc/web/host_referrallimit'], 10) || 100);
				this._hostInfo.set('disabled', empty);

				var isIE89 = (has('ie') == 8 || has('ie') == 9);
				if (empty && isIE89) {
					// prevent IE displaying a disabled button with a shadowed text
					domAttr.set(this._hostInfo.focusNode, 'disabled', false);
				}

				if (empty) {
					return;
				}
				array.forEach(data.result, function(hostname) {
					this._hostMenu.addChild(new MenuItem({
						label: hostname,
						disabled: hostname === fqdn,
						onClick: lang.hitch(this, '_switchUMC', hostname)
					}));
				}, this);
			}));
		},

		_switchUMC: function(hostname) {
			topic.publish('/umc/actions', 'host-switch');
			tools.openRemoteSession(hostname);
		},

		_showAboutDialog: function() {
			var _formatDate = function(timestamp) {
				return locale.format(new Date(timestamp), {
					fullYear: true,
					timePattern: " ",
					formatLength: "long"
				});
			};

			// query data from server
			topic.publish('/umc/actions', 'menu-help', 'about');
			tools.umcpCommand('get/info').then(function(response) {
				var data = response.result;
				array.forEach(['ssl_validity_host', 'ssl_validity_root'], function(ikey) {
					data[ikey] = _formatDate(data[ikey]);
				});
				data.path = require.toUrl('umc/app');
				dialog.templateDialog('umc/app', 'about.' + _getLang() + '.html', data, _('About UMC'), _('Close'));
			});
		},

		_showHelpDialog: function() {
			topic.publish('/umc/actions', 'menu-help', 'help');
			dialog.templateDialog('umc/app', 'help.' + _getLang()  + '.html', {
				path: require.toUrl('umc/app')
			}, _('Help'), _('Close'));
		},

		_showFeedbackPage: function() {
			topic.publish('/umc/actions', 'menu-help', 'feedback');
			var url = _('umcFeedbackUrl') + '?umc=' + require('umc/app')._tabContainer.get('selectedChildWidget').title;
			var w = window.open(url, 'umcFeedback');
			w.focus();
		}
	});

	var app = new declare([Evented], {
		start: function(/*Object*/ props) {
			// summary:
			//		Start the UMC, i.e., render layout, request login for a new session etc.
			// props: Object
			//		The following properties may be given:
			//		* username, password: if both values are given, the UMC tries to directly
			//		  with these credentials.
			//		* module, flavor: if module is given, the module is started immediately,
			//		  flavor is optional.
			//		* overview: if false and a module is given for autostart, the overview and module header will
			//		  not been shown and the module cannot be closed

			// save some config properties
			tools.status('overview', tools.isTrue(props.overview));
			// username will be overriden by final authenticated username
			tools.status('username', props.username || cookie('UMCUsername'));
			// password has been given in the query string... in this case we may cache it, as well
			tools.status('password', props.password);

			if (typeof props.module == "string") {
				// a startup module is specified
				tools.status('autoStartModule', props.module);
				tools.status('autoStartFlavor', typeof props.flavor == "string" ? props.flavor : null);
			}

			if (props.username && props.password && typeof props.username == "string" && typeof props.password == "string") {
				// username and password are given, try to login directly
				this.login();
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
				tools.umcpCommand('set', {}, false).then(lang.hitch(this, function() {
					// session is still valid
					this.onLogin(cookie('UMCUsername'));
				}), lang.hitch(this, function() {
					this.login();
				}));
			}
			else {
				this.login();
			}
		},

		login: function() {
			return dialog.login().then(lang.hitch(this, 'onLogin')).always(lang.hitch(this, function() {
				if (dialog._loginDialog) {
					// display the UCS logo animation some time
					setTimeout(function() {
						dialog._loginDialog.hide();
					}, 1500);
				}
			}));
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
			return this.load();
		},

		_tabContainer: null,
		_topContainer: null,
		_overviewPage: null,
		_categoriesContainer: null,
		_setupStaticGui: false,
		_moduleStore: null,
		_categories: [],
		_loaded: false,

		setupStaticGui: function() {
			// setup everything that can be set up statically

			// make sure that we have not build the GUI before
			if (this._setupStaticGui) {
				return;
			}

			if (has('touch')) {
				this.setupTouchDevices();
			}

			if (!tools.status('overview')) {
				domClass.toggle(baseWin.body(), 'umcHeadless', true);
			}

			// set up fundamental layout parts...

			this._topContainer = new ContainerWidget({
				id: 'umcTopContainer',
				domNode: dom.byId('umcTopContainer'),
				containerNode: dom.byId('umcTopContainer'),
				'class': 'umcTopContainer'
//				style: styleStr
			});

			// the header
			this._header = new UmcHeader({
				id: 'umcHeader',
				'class': 'umcHeader'
			});

			// module (and overview) container
			this._tabContainer = new StackContainer({
				'class': 'umcMainTabContainer dijitTabContainer dijitTabContainerTop'
			});

			// the tab bar
			this._tabController = new TabController({
				'class': 'umcMainTabController dijitTabContainer dijitTabContainerTop-tabs dijitHidden',
				containerId: this._tabContainer.id
			});

			this.registerTabSwitchHandling();

			// put everything together
			this._topContainer.addChild(this._tabController, 0);
			this._topContainer.addChild(this._header);
			this._topContainer.addChild(dialog.createNotificationMaster());
			this._topContainer.addChild(this._tabContainer);
			this._topContainer.startup();
			//this._updateScrolling();

			// subscribe to requests for opening modules and closing/focusing tabs
			topic.subscribe('/umc/modules/open', lang.hitch(this, 'openModule'));
			topic.subscribe('/umc/tabs/close', lang.hitch(this, 'closeTab'));
			topic.subscribe('/umc/tabs/focus', lang.hitch(this, 'focusTab'));

			var deferred = new Deferred();
			topic.subscribe('/umc/module/startup', function(callback) {
				deferred.then(callback);
			});
			on.once(this, 'ModulesLoaded', lang.hitch(this, function() {
				// run some checks (only if a overview page is available)
				deferred.resolve(tools.status('overview'));
				if (tools.status('overview')) {
					topic.publish('/umc/started');
				}
			}));

			this._setupStaticGui = true;
		},

		setupTouchDevices: function() {
			// add specific CSS class for touch devices (e.g., tablets)
			domClass.add(baseWin.body(), 'umcTouchDevices');
		},

		registerTabSwitchHandling: function() {
			// register events for closing and focusing
			this._tabContainer.watch('selectedChildWidget', lang.hitch(this, function(name, oldModule, newModule) {
				this._lastSelectedChild = oldModule;
				if (!newModule.moduleID) {
					// this is the overview page, not a module
					topic.publish('/umc/actions', 'overview');
				} else {
					topic.publish('/umc/actions', newModule.moduleID, newModule.moduleFlavor, 'focus');
				}
				var overviewShown = (newModule === this._overviewPage);
				domClass.toggle(baseWin.body(), 'umcOverviewShown', overviewShown);
				domClass.toggle(baseWin.body(), 'umcOverviewNotShown', !overviewShown);
				domClass.toggle(this._tabController.domNode, 'dijitHidden', (this._tabContainer.getChildren().length <= 1)); // hide/show tabbar
				if (newModule.selectedChildWidget && newModule.selectedChildWidget._onShow) {
					newModule.selectedChildWidget._onShow();
				}
			}));
			aspect.before(this._tabContainer, 'removeChild', lang.hitch(this, function(module) {
				topic.publish('/umc/actions', module.moduleID, module.moduleFlavor, 'close');
				if (module == this._tabContainer.get('selectedChildWidget')) {
					if (array.indexOf(this._tabContainer.getChildren(), this._lastSelectedChild) !== -1) {
						this._tabContainer.selectChild(this._lastSelectedChild);
					} else {
						this.switchToOverview();
					}
				}
			}));
		},

		switchToOverview: function() {
			if (array.indexOf(this._tabContainer.getChildren(), this._overviewPage) < 0) {
				return;  // overview is not displayed
			}
		//	topic.publish('/umc/actions', 'overview');
			this._tabContainer.selectChild(this._overviewPage);
		},

		load: function() {
			// make sure that we don't load the modules twice
			if (this._loaded) {
				this.onLoaded();
				return;
			}

			// load data dynamically
			var ucrDeferred = this._loadUcrVariables();
			var modulesDeferred = this._loadModules().then(lang.hitch(this, '_initModuleStore'));

			// wait for modules and the UCR variables to load
			return all([modulesDeferred, ucrDeferred]).then(lang.hitch(this, function() {
				this._loaded = true;
				this.onLoaded();
			}), lang.hitch(this, function() {
				// something went wrong... try to login again
				this.login();
			}));
		},

		_loadUcrVariables: function() {
			return tools.ucr([
				'server/role',
				'system/setup/showloginmessage', // set to true when not joined
				'domainname',
				'hostname',
				'umc/web/feedback/mail',
				'umc/web/feedback/description',
				'umc/web/favorites/default',
				'umc/web/startupdialog',
				'umc/web/host_referrallimit',
				'umc/web/sso/enabled',
				'umc/web/sso/allow/http',
				'umc/web/sso/newwindow',
				'umc/http/session/timeout',
				'ssl/validity/host',
				'ssl/validity/root',
				'ssl/validity/warning',
				'update/available',
				'update/reboot/required',
				'umc/web/piwik',
				'license/base',
				'uuid/license',
				'version/releasename',
				'version/erratalevel',
				'version/patchlevel',
				'version/version'
			]).then(lang.hitch(this, function(res) {
				// save the ucr variables in a local variable
				lang.mixin(_ucr, res);
				this._loadPiwik();
				this._saveVersionStatus();
				tools.status('umcWebSsoEnabled', _ucr['umc/web/sso/enabled']);
				tools.status('umcWebSsoAllowHttp', _ucr['umc/web/sso/allow/http']);
				tools.status('umcWebSsoNewwindow', _ucr['umc/web/sso/newwindow']);
			}));
		},

		_loadPiwik: function() {
			var piwikUcrv = _ucr['umc/web/piwik'];
			var piwikUcrvIsSet = typeof piwikUcrv == 'string' && piwikUcrv !== '';
			tools.status('hasFFPULicense', _hasFFPULicense());
			if (tools.isTrue(_ucr['umc/web/piwik']) || (!piwikUcrvIsSet && _hasFFPULicense())) {
				// use piwik for user action feedback if it is not switched off explicitely
				tools.status('piwikDisabled', false);
				require(["umc/piwik"], function() {});
			} else {
				tools.status('piwikDisabled', true);
			}
		},

		_saveVersionStatus: function() {
			tools.status('ucsVersion', lang.replace('{version/version}-{version/patchlevel} errata{version/erratalevel} ({version/releasename})', _ucr));
		},

		reloadModules: function() {
			return this._loadModules(true).then(lang.hitch(this, function(args) {
				var modules = args[0];
				var categories = args[1];

//				when(this._moduleStore.query(), lang.hitch(this, function(items) {
//					// undefine JS modules and remove modules from module store
//					array.forEach(items, function(module) {
//						this._moduleStore.remove(module.$id$);
//						require.undef('umc/modules/' + module.id);  // FIXME: everything starting with …/module.id
//					}, this);

					this._grid.set('categories', categories);
					this._moduleStore.constructor(modules, categories);

					this._overviewPage.removeChild(this._categoryButtons);
					this.renderCategories();
					// select the previous selected category again (assuming it still exists after reload)
					this._updateQuery(this.category || {id: '_favorites_'});
//				}));
			}));
		},

		_loadModules: function(reload) {
			var options = reload ? {reload: true} : null;
			var onlyLoadAutoStartModule = !tools.status('overview') && tools.status('autoStartModule');
			return all({
				modules: tools.umcpCommand('get/modules/list', options, false),
				categories: tools.umcpCommand('get/categories/list', undefined, false)
			}).then(lang.hitch(this, function(data) {
				// update progress
				var _modules = lang.getObject('modules.modules', false, data) || [];
				var _categories = lang.getObject('categories.categories', false, data) || [];

				if (onlyLoadAutoStartModule) {
					_modules = array.filter(_modules, function(imod) {
						var moduleMatched = tools.status('autoStartModule') == imod.id;
						var flavorMatched = !tools.status('autoStartFlavor') || tools.status('autoStartFlavor') == imod.flavor;
						return moduleMatched && flavorMatched;
					});
				}

				this._loadJavascriptModules(_modules);

				return [_modules, _categories];
			}));
		},

		_initModuleStore: function(args) {
			var modules = args[0];
			var categories = args[1];
			this._moduleStore = this._createModuleStore(modules, categories);
		},

		_createModuleStore: function(modules, categories) {
			return new Observable(new _ModuleStore(modules, categories));
		},

		_loadJavascriptModules: function(modules) {
			// register error handler
			require.on('error', function(err) {
				if (err.message == 'scriptError') {
					dialog.warn(_('Could not load module "%s".', err.info[0]));
					console.log('scriptError:', err);
				}
			});

			var loadedCount = [];

			tools.forEachAsync(modules, lang.hitch(this, function(imod) {
				loadedCount.push(this._tryLoadingModule(imod));
			})).then(lang.hitch(this, function() {
				all(loadedCount).always(lang.hitch(this, 'onModulesLoaded'));
			}));
		},

		_tryLoadingModule: function(module) {
			var deferred = new Deferred();
			try {
				require(['umc/modules/' + module.id], lang.hitch(this, function(baseClass) {
					if (typeof baseClass == "function" && tools.inheritsFrom(baseClass.prototype, 'umc.widgets._ModuleMixin')) {
						deferred.resolve(baseClass);
					} else {
						deferred.cancel(new Error(module.id + ' is not a umc.widgets._ModuleMixin!'));
					}
				}));
			} catch (err) {
				deferred.cancel(err);
			}
			return deferred;
		},

		onLoaded: function() {
			// updated status information from ucr variables
			tools.status('sessionTimeout', parseInt(_ucr['umc/http/session/timeout'], 10) || tools.status('sessionTimeout'));
			tools.status('feedbackAddress', _ucr['umc/web/feedback/mail'] || tools.status('feedbackAddress'));
			tools.status('feedbackSubject', _ucr['umc/web/feedback/description'] || tools.status('feedbackSubject'));

//			on.once(this, 'GuiDone', lang.hitch(this, function() {
//				this._tabContainer.layout();
//
//				// put focus into the GalleryPane for scrolling
//				dijit.focus(this._categoryPane.domNode);
//				this.on(_categoryPane, 'show', function() {
//					dijit.focus(this._categoryPane.domNode);
//				});
//			}));

			var launchableModules = this._getLaunchableModules();
			tools.status('singleModule', launchableModules.length < 2);

			this.setupGui();

			if (!launchableModules.length) {
				dialog.alert(_('There is no module available for the authenticated user %s.', tools.status('username')));
			} else if (launchableModules.length === 1) {
				// if only one module exists open it
				var module = launchableModules[0];
				this.openModule(module.id, module.flavor);
			} else if (tools.status('autoStartModule')) {
				// if module is given in the query string, open it directly
				this.openModule(tools.status('autoStartModule'), tools.status('autoStartFlavor'));
			}
		},

		setupGui: function() {
			// make sure that we have not build the GUI before
			if (tools.status('setupGui')) {
				return;
			}

			// save hostname and domainname as status information
			tools.status('domainname', _ucr.domainname);
			tools.status('hostname', _ucr.hostname);
			tools.status('fqdn', _ucr.hostname + '.' + _ucr.domainname);

			window.document.title = lang.replace('{0} - {1}', [tools.status('fqdn'), window.document.title]);

			// setup menus
			this._header.setupGui();
			this._setupOverviewPage();

			// set a flag that GUI has been build up
			tools.status('setupGui', true);
			this.onGuiDone();
		},

		_setupOverviewPage: function() {
			if (!tools.status('overview')) {
				// no overview page is being displayed
				// (e.g., system setup in appliance scenario)
				return;
			}

			this._grid = new _OverviewPane({
				'class': 'umcOverviewPane',
//				categories: this.getCategories(),
				store: this._moduleStore,
				actions: [{
					name: 'open',
					label: _('Open module'),
					isDefaultAction: true,
					callback: lang.hitch(this, function(id, item) {
						this.openModule(item);
					})
				}, {
					name: 'toggle_favorites',
					label: function(item) {
						return isFavorite(item) ? _('Remove from favorites') : _('Add to favorites');
					},
					callback: lang.hitch(this, function(id, item) {
						this._toggleFavoriteModule(item);
					})
				}]
			});

			this._overviewPage = new Page({
				noFooter: true,
				id: 'umcOverviewPage',
				title: 'Overview',
				'class': 'umcOverviewContainer container'
			});

			this._searchText = new Text({
				'class': 'dijitHidden umcGalleryCategoryHeader'
			});

			this.renderCategories();
			this._overviewPage.addChild(this._searchText);
			this._overviewPage.addChild(this._grid);
			this._tabContainer.addChild(this._overviewPage, 0);
			this._tabController.hideChild(this._overviewPage);

			aspect.after(this._overviewPage, '_onShow', lang.hitch(this, '_focusSearchField'));
			this._registerGridEvents();
			this._updateQuery({id: '_favorites_'});
		},

		renderCategories: function() {
			this._categoryButtons = new ContainerWidget({
				'class': 'umcCategoryBar'
			});
			this._overviewPage.addChild(this._categoryButtons, 0);
			array.forEach(this.getCategories(), lang.hitch(this, function(category) {
				var iconClass = '';
				if (category.icon) {
					iconClass = tools.getIconClass(category.icon, 70);
				}
				var color = category.color || 'white';
				styles.insertCssRule(lang.replace('.umcGalleryWrapperItem .umcGalleryCategory-{id}:hover, .umcGalleryWrapperItem.umcGalleryItemActive .umcGalleryCategory-{id}', category), lang.replace('background-color: {0}; ', [color]));
				var button = new CategoryButton({
					label: category.label,
					'class': lang.replace('umcCategory-{id}', category),
					onClick: lang.hitch(this, '_updateQuery', category),
					color: color,
					categoryID: category.id,
					iconClass: iconClass
				});
				category._button = button;
				this._categoryButtons.addChild(button);
			}));

			// spread category buttons over whole width
			styles.insertCssRule('.umc .umcCategoryBar .dijitButton', lang.replace('width: {0}%', [100.0 / this.getCategories().length]));
		},

		_focusSearchField: function() {
			if (!this._header._searchSidebar) {
				return;
			}
			if (!has('touch')) {
				setTimeout(lang.hitch(this, function() {
					this._header._searchSidebar.focus();
				}, 0));
			}
		},

		_registerGridEvents: function() {
			if (!this._header._searchSidebar) {
				return;
			}
			this._header._searchSidebar.on('search', lang.hitch(this, function() {
				this.switchToOverview();
				this._updateQuery(null);
			}));
		},

		_updateQuery: function(category) {
			this.category = category;
			var searchPattern = '';
			var searchQuery = new RegExp('.*');

			// update the 'selected' state of all category buttons
			array.forEach(this._categoryButtons.getChildren(), function(ibutton) {
				ibutton.set('selected', category ? ibutton.categoryID == category.id : false);
			});

			if (!category) {
				searchPattern = lang.trim(this._header._searchSidebar.get('value'));
				searchQuery = this._header._searchSidebar.getSearchQuery(searchPattern);
			} else {
				if (this._header._searchSidebar) {
					this._header._searchSidebar.set('value', null);
				}
			}
			this._grid.updateQuery(searchPattern, searchQuery, category);

			// update the search label
			domClass.toggle(this._searchText.domNode, 'dijitHidden', !!category);
			this._searchText.set('content', _('Search query ›%s‹', entities.encode(searchPattern)));
		},

		openModule: function(/*String|Object*/ module, /*String?*/ flavor, /*Object?*/ props) {
			// summary:
			//		Open a new tab for the given module.
			// description:
			//		This method is subscribed to the channel '/umc/modules/open' in order to
			//		open modules from other modules without requiring 'umc/app'.
			// module:
			//		Module ID as string
			// flavor:
			//		The module flavor as string.
			// props:
			//		Optional properties that are handed over to the module constructor.

			var deferred = new Deferred();
			// get the object in case we have a string
			if (typeof(module) == 'string') {
				module = this.getModule(module, flavor);
			}
			if (undefined === module) {
				deferred.reject();
				return deferred;
			}

			this._tryLoadingModule(module).then(lang.hitch(this, function(BaseClass) {
				// force any tooltip to hide
				if (Tooltip._masterTT) { Tooltip._masterTT.fadeOut.play(); }

				// create a new tab
				var tab = null; // will be the module
				if (BaseClass.prototype.unique) {
					var sameModules = array.filter(this._tabContainer.getChildren(), function(i) {
						return i.moduleID == module.id && i.moduleFlavor == module.flavor;
					});
					if (sameModules.length) {
						tab = sameModules[0];
					}
				}
				if (!tab) {
					// module is not open yet, open it
					var params = lang.mixin({
						title: module.name,
						//iconClass: tools.getIconClass(module.icon),
						closable: tools.status('overview') && !tools.status('singleModule'),  // closing tabs is only enabled if the overview is visible
						moduleFlavor: module.flavor,
						moduleID: module.id,
						description: module.description
					}, props);
					tab = new BaseClass(params);
					this._tabContainer.addChild(tab);
					tab.startup();
					tools.checkReloadRequired();

					this.__insertTabStyles(tab, module);
				}
				this._tabContainer.selectChild(tab, true);
				deferred.resolve(tab);
			})).otherwise(function(err) {
				console.warn('Error initializing module ' + module.id + ':', err);
				tools.checkReloadRequired();
				deferred.reject(err);
			});
			return deferred;
		},

		__insertTabStyles: function(tab, module) {
			var module_flavor_css = module.id;
			if (module.flavor) {
				module_flavor_css = lang.replace('{id}-{flavor}', module);
			}
			module_flavor_css = module_flavor_css.replace(/[^_a-zA-Z0-9\-]/g, '-');
			var color = this.__getModuleColor(module);
			var defaultClasses = '.umc .dijitTabContainerTop-tabs .dijitTab';
			var cssProperties = lang.replace('background-color: {0}; background-image: none; filter: none;', [color]);

			domClass.add(tab.controlButton.domNode, lang.replace('umcModuleTab-{0}', [module_flavor_css]));
			styles.insertCssRule(lang.replace('{0}.umcModuleTab-{1}.dijitHover', [defaultClasses, module_flavor_css]), cssProperties);
			styles.insertCssRule(lang.replace('{0}.umcModuleTab-{1}.dijitTabChecked', [defaultClasses, module_flavor_css]), cssProperties);
			styles.insertCssRule(lang.replace('.umcModuleHeader-{0}', [module_flavor_css]), cssProperties);
		},

		__getModuleColor: function(module) {
			var category = array.filter(this.getCategories(), lang.hitch(this, function(category) {
				if (category.id != '_favorites_' && array.indexOf(module.categories, category.id) >= 0) {
					return true;
				}
				return false;
			}));
			if (category.length) {
				return category[0].color;
			}
			return '';
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

		getModules: function(/*String?*/ category) {
			// summary:
			//		Get modules, either all or the ones for the specific category.
			//		The returned array contains objects with the properties
			//		{ BaseClass, id, title, description, categories }.
			// categoryID:
			//		Optional category name.a
			return this._moduleStore.getModules(category);
		},

		_getLaunchableModules: function() {
			return this._moduleStore.query(function(item) {
				return item.category !== '_favorites_';
			});
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
			return this._moduleStore.getModule(id, flavor, category);
		},

		getCategories: function() {
			// summary:
			//		Get all categories as an array. Each entry has the following properties:
			//		{ id, description }.
			return this._moduleStore.getCategories();
		},

		getCategory: function(/*String*/ id) {
			// summary:
			//		Get the category that corresponds to the given ID.
			return this._moduleStore.getCategory(id);
		},

		addFavoriteModule: function(/*String*/ id, /*String?*/ flavor) {
			if (!_favoritesDisabled) {
				this._moduleStore.addFavoriteModule(id, flavor);
			}
		},

		_toggleFavoriteModule: function(module) {
			if (isFavorite(module)) {
				// for the favorite category, remove the moduel from the favorites
				this._moduleStore.removeFavoriteModule(module.id, module.flavor);
				topic.publish('/umc/actions', 'overview', 'favorites', module.id, module.flavor, 'remove');
			}
			else {
				// for any other category, add the module to the favorites
				this._moduleStore.addFavoriteModule(module.id, module.flavor);
				topic.publish('/umc/actions', 'overview', 'favorites', module.id, module.flavor, 'add');
			}
		},

		_disablePiwik: function(disable) {
			// FIXME: where is it used
			topic.publish('/umc/piwik/disable', disable);
		},

		addMenuEntry: function(item) {
			if (this._header) {
				this._header.addMenuEntry(item);
			}
		},

		registerOnStartup: function(/*Function*/ callback) {
			topic.publish('/umc/module/startup', callback);
		},

		relogin: function(username) {
			dialog.confirm(_('Do you really want to logout?'), [{
				label: _('Cancel')
			}, {
				label: _('Logout'),
				'default': true,
				callback: lang.hitch(this, function() {
					topic.publish('/umc/actions', 'session', 'logout');
					tools.closeSession();
					if (username === undefined) {
						window.location.reload(true);
					} else {
						window.location.search = 'username=' + username;
					}
				})
			}]);
		},

		linkToModule: function(/*String*/ moduleId, /*String?*/ moduleFlavor, /*String?*/ linkName) {
			kernel.deprecated('umc/app:linkToModule()', 'use tools.linkToModule instead (different argument format)!');
			return tools.linkToModule({
				module: moduleId,
				flavor: moduleFlavor,
				linkName: linkName
			});
		},

		__openAllModules: function(category) {
			umc.app._moduleStore.query(function(m) {
				if (category) {
					return m.category == category;
				}
				return m.category && m.category !== '_favorites_';
			}).forEach(function(m) {
				umc.app.openModule(m.id, m.flavor);
			});
		},

		onModulesLoaded: function() {
			// event stub when all modules are loaded as Javascript files
		},

		onGuiDone: function() {
			// event stub
		}
	})();

	lang.setObject('umc.app', app);
	return app;
});
