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
/*global define require console window getQuery setTimeout*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/query",
	"dojo/window",
	"dojo/on",
	"dojo/aspect",
	"dojo/has",
	"dojo/string",
	"dojo/Evented",
	"dojo/Deferred",
	"dojo/when",
	"dojo/promise/all",
	"dojo/cookie",
	"dojo/topic",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dojo/dom-style",
	"dojo/dom-attr",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/dom-construct",
	"dojo/date/locale",
	"dijit/Dialog",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/CheckedMenuItem",
	"dijit/MenuSeparator",
	"dijit/Tooltip",
	"dijit/form/DropDownButton",
	"dijit/layout/BorderContainer",
	"dijit/layout/TabContainer",
	"dijit/layout/StackContainer",
	"dijit/registry",
	"umc/tools",
	"umc/dialog",
	"umc/store",
	"umc/widgets/ProgressInfo",
	"umc/widgets/LiveSearchSidebar",
	"umc/widgets/GalleryPane",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/widgets/Tooltip",
	"umc/i18n!",
	"dojo/sniff" // has("ie"), has("ff")
], function(declare, lang, kernel, array, baseWin, query, win, on, aspect, has, string, Evented, Deferred, when, all, cookie, topic, Memory, Observable, style, domAttr, domClass, domGeometry, domConstruct, locale, Dialog, Menu, MenuItem, CheckedMenuItem, MenuSeparator, Tooltip, DropDownButton, BorderContainer, TabContainer, StackContainer, registry, tools, dialog, store, ProgressInfo, LiveSearchSidebar, GalleryPane, ContainerWidget, Page, Text, Button, UMCTooltip, _) {
	// cache UCR variables
	var _ucr = {};
	var _userPreferences = {};
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
	var isInCategoryFavorites = function(mod) {
		return mod.category == '_favorites_';
	};


	var _OverviewPane = declare([ GalleryPane ], {
		categories: null,

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

		_onNotification: function() {
			this._updateCategoryHeaderVisiblity(this._lastCollection);
		},

		_getCategory: function(categoryID) {
			var categories = array.filter(this.categories, function(icat) {
				return icat.id == categoryID;
			});
			if (!categories.length) {
				return null;
			}
			return categories[0];
		},

		renderRow: function(item, options) {
			var row = this.inherited(arguments);
			if (item._isSeparator) {
				var category = this._getCategory(item.category);
				row = domConstruct.create('div', {
					'class': 'umcGalleryCategoryHeader',
					innerHTML: category.label,
					'categoryID': category.id
				});
			}
			return row;
		},

		_updateCategoryHeaderVisiblity: function(items) {
			query('.umcGalleryCategoryHeader', this.contentNode).forEach(function(inode) {
				var category = domAttr.get(inode, 'categoryID');
				var hasItems = array.some(items, function(iitem) {
					return !iitem._isSeparator && iitem.category == category;
				});
				style.set(inode, 'display', hasItems ? 'block' : 'none');
			});
		},

		renderArray: function(items) {
			var result = this.inherited(arguments);
			this._updateCategoryHeaderVisiblity(items);
			return result;
		},

		getItemDescription: function(item) {
			return item.description;
		},

		updateQuery: function(searchPattern, searchQuery, category) {
			var query = function(obj) {
				// sub conditions
				var allCategories = category.id == '_all_';
				var displayItem = obj._isSeparator || obj.BaseClass;
				var matchesPattern = obj._isSeparator || !searchPattern
					// for a given pattern, ignore 'pseudo' entries in _favorites_ category
					|| (searchQuery.test(null, obj) && obj.category != '_favorites_');
				var matchesCategory = obj.category == category.id;
				if (allCategories) {
					matchesCategory = true;
				}
				//else if (category.id == '_favorites_') {
				//	// allow all separators AND favorite items of categories != _favorites_
				//	matchesCategory = obj.category != '_favorites_' && (obj._isSeparator || obj._isFavorite);
				//}

				// match separators OR modules with a valid class
				return displayItem && matchesPattern && matchesCategory;
			};

			// set query
			this.set('query', query);
		}
	});


	var _ProgressDialog = declare([Dialog], {
		_progressInfo: null,
		postMixInProperties: function() {
			this.inherited(arguments);
			this.content = this._progressInfo = new ProgressInfo({});
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._progressInfo.updateTitle(_('Loading modules'));
			this._progressInfo.updateInfo('&nbsp;');
			this.set('closable', false); // need to be set explicitely
		},

		_setMaximumAttr: function(value) {
			this._set('maximum', value);
			this._progressInfo.update(0);
		},

		update: function(ndeps, moduleName) {
			this._progressInfo.update(100 * ndeps / this.maximum, moduleName ? _('Loaded module %s', moduleName) : '&nbsp;');
		},

		close: function() {
			var hideDeferred = this.hide();
			if (hideDeferred) {
				return hideDeferred.then(lang.hitch(this, 'destroyRecursive'));
			}
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
			this._addFavoriteCategory();
			this._addSeparatorItems();
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
			var nonEmptyCategories = {};
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

		_addSeparatorItems: function() {
			array.forEach(this.categories, function(icat) {
				this.put(this._createModuleItem({
					id: '_separator_',
					name: '',
					description: '',
					_isSeparator: true
				}, icat.id));
			}, this);
		},

		_addFavoriteCategory: function() {
			this.categories.unshift({
				label: _('Favorites'),
				id: '_favorites_',
				priority: Number.POSITIVE_INFINITY
			});
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
			tools.setUserPreference({favorites: favoritesStr});
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
				// update _isFavorite flag
				_mod._isFavorite = true;
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

			// update _isFavorite module
			var mod = this.getModule(id, flavor);
			if (mod && mod._isFavorite) {
				mod._isFavorite = false;
				this.put(mod);
			}

			// save settings
			this._saveFavorites();
		}
	});

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
				tools.status('autoStartModule', props.module);
				tools.status('autoStartFlavor', typeof props.flavor == "string" ? props.flavor : null);
				on.once(this, 'GuiDone', lang.hitch(this, function() {
					var hasOnlyOneModule = this._getLaunchableModules().length == 1;
					if (hasOnlyOneModule) {
						// this module is launched automatically anyways
						return;
					}

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
			this.load();
		},

		_tabContainer: null,
		_topContainer: null,
		_overviewPage: null,
		_helpMenu: null,
		_headerRight: null,
		_settingsMenu: null,
		_hostInfo: null,
		_categoriesContainer: null,

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

			// get the object in case we have a string
			if (typeof(module) == 'string') {
				module = this.getModule(module, flavor);
			}
			if (undefined === module) {
				return undefined;
			}

			// create a new tab
			try {
				// force any tooltip to hide
				Tooltip._masterTT && Tooltip._masterTT.fadeOut.play();

				var tab = undefined; // will be the module
				if (module.BaseClass.prototype.unique) {
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
						iconClass: tools.getIconClass(module.icon),
						closable: tools.status('overview'),  // closing tabs is only enabled if the overview is visible
						moduleFlavor: module.flavor,
						moduleID: module.id,
						description: module.description
					}, props);
					tab = new module.BaseClass(params);
					this._tabContainer.addChild(tab);
					tab.startup();
					tools.checkReloadRequired();
				}
				this._tabContainer.selectChild(tab, true);
				return tab;
			} catch (err) {
				console.warn('Error initializing module ' + module.id + ':', err);
				tools.checkReloadRequired();
				return undefined;
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

		onLoaded: function() {
			// updated status information from ucr variables
			tools.status('sessionTimeout', parseInt( _ucr['umc/http/session/timeout'] , 10 ) || tools.status('sessionTimeout'));
			tools.status('feedbackAddress', _ucr['umc/web/feedback/mail'] || tools.status('feedbackAddress'));
			tools.status('feedbackSubject', _ucr['umc/web/feedback/description'] || tools.status('feedbackSubject'));

			this.setupGui();

			// if only one module exists open it
			var launchableModules = this._getLaunchableModules();
			if (launchableModules.length === 1) {
				var module = launchableModules[0];
				this.openModule(module.id, module.flavor);
			}
		},

		_moduleStore: null,
		_categories: [],
		_loaded: false,
		load: function() {
			// make sure that we don't load the modules twice
			if (this._loaded) {
				this.onLoaded();
				return;
			}

			// load data dynamically
			var progressDialog = new _ProgressDialog({});
			var ucrDeferred = this._loadUcrVariables();
			var userPreferencesDefered = this._loadUserPreferences();
			var modulesDeferred = this._loadModules(progressDialog).then(lang.hitch(this, '_initModuleStore'));

			// wait for modules, the UCR variables, and user preferences to load
			var load = all([modulesDeferred, ucrDeferred, userPreferencesDefered]).then(lang.hitch(this, function() {
				// loading is done
				this._moduleStore.setFavoritesString(_userPreferences.favorites || _ucr['umc/web/favorites/default']);
				when(progressDialog.close(), lang.hitch(this, function() {
					this._loaded = true;
					this.onLoaded();
				}));
			}), lang.hitch(this, function() {
				// something went wrong... try to login again
				when(progressDialog.close(), lang.hitch(this, function() {
					dialog.login().then(lang.hitch(this, 'onLogin'));
				}));
			}));

			// perform actions that depend on the UCR variables
			ucrDeferred.then(function(res) {
			});

			return load;
		},

		reloadModules: function() {
			var progressDialog = new _ProgressDialog({});
			progressDialog.show();

			var userPreferencesDefered = this._loadUserPreferences();
			var modulesDeferred = this._loadModules(progressDialog, true).then(lang.hitch(this, '_reloadModuleStore'));
			var reload = all([modulesDeferred, userPreferencesDefered]);
			reload.then(lang.hitch(this, function() {
				this._setupOverviewSearchSidebarCategories();
				this._moduleStore.setFavoritesString(_userPreferences.favorites || _ucr['umc/web/favorites/default']);
			}));
			reload.always(lang.hitch(progressDialog, 'close'));
			return reload;
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

		_loadUserPreferences: function() {
			return tools.getUserPreferences().then(lang.hitch(this, function(prefs) {
				// save the preferences in a local variable
				lang.mixin(_userPreferences, prefs);
			})).then(function() {
				// nothing to do
				_favoritesDisabled = false;
			}, function() {
				_favoritesDisabled = true;
			});
		},

		_loadModules: function(progressDialog, reload) {
			var options = reload ? {reload: true} : null;
			var onlyLoadAutoStartModule = !tools.status('overview') && tools.status('autoStartModule');
			if (!onlyLoadAutoStartModule) {
				progressDialog.show();
			}
			return tools.umcpCommand('get/modules/list', options, false).then(lang.hitch(this, function(data) {
				// update progress
				var _modules = lang.getObject('modules', false, data) || [];
				var modules = [];

				if (onlyLoadAutoStartModule) {
					_modules = array.filter(_modules, function(imod) {
						var moduleMatched = tools.status('autoStartModule') == imod.id;
						var flavorMatched = !tools.status('autoStartFlavor') || tools.status('autoStartFlavor') == imod.flavor;
						return moduleMatched && flavorMatched;
					});
				}

				var ndeps = 0;
				var modulesLoadedDeferred = new Deferred();
				var modulesLoaded = {};
				var nModules = 0;
				array.forEach(_modules, function(imod) {
					if (modulesLoaded[imod.id] === undefined) {
						// do not count flavors multiple times
						++nModules;
						modulesLoaded[imod.id] = {
							loaded: false,
							loadedFlavors: 0,
							nFlavors: 0
						};
					}
					if (imod.flavor) {
						++modulesLoaded[imod.id].nFlavors;
					}
				});
				progressDialog.set('maximum', nModules);

				var markModuleAsLoaded = function(module) {
					modulesLoaded[module.id].loaded = true;
					if (module.flavor) {
						++modulesLoaded[module.id].loadedFlavors;
					}
				};

				var getNumOfModulesLoaded = function() {
					var nLoaded = 0;
					tools.forIn(modulesLoaded, function(ikey, istate) {
						if (istate.nFlavors) {
							// module has flavors... count flavors
							nLoaded += istate.loadedFlavors / istate.nFlavors;
						}
						else if (istate.loaded) {
							// no flavors
							++nLoaded;
						}
					});
					return nLoaded;
				};

				var matchModuleByPath = function(path) {
					var mod = null;
					tools.forIn(modulesLoaded, function(ikey, iloaded) {
						var ipath = lang.replace('umc/modules/{0}.js', [ikey]);
						var idx = path.indexOf(ipath);
						var pathMatches = idx + ipath.length == path.length;
						if (pathMatches) {
							var matchingModules = array.filter(_modules, function(imod) {
								return imod.id == ikey;
							});
							if (matchingModules.length) {
								mod = matchingModules[0];
								return false;
							}
						}
					});
					return mod;
				};

				var incDeps = function(module) {
					// helper function
					if (module) {
						markModuleAsLoaded(module);
					}
					var nModulesLoaded = getNumOfModulesLoaded();
					progressDialog.update(nModulesLoaded, module ? module.name : '');
					if (nModulesLoaded >= nModules) {
						modulesLoadedDeferred.resolve([modules, data.categories]);
					}
				};

				// register error handler
				require.on('error', function(err) {
					// count the loaded dependencies
					if (err.message == 'scriptError') {
						var mod = matchModuleByPath(err.info[0]);
						if (mod) {
							incDeps(mod);
						}
					}
				});

				// get all modules
				tools.forEachAsync(_modules, function(imod, i) {
					this._tryLoadingModule(imod, i).then(lang.hitch(this, function(loadedModule) {
						modules.push(loadedModule);
						incDeps(imod);
					}), function(err) {
						console.warn('Error loading module ' + imod.id + ':', err);
						incDeps(imod);
					});
				}, this);

				// resolve the deferred object directly if there are no modules available
				if (!_modules.length) {
					incDeps();
				}

				return modulesLoadedDeferred;
			}));
		},
		
		_initModuleStore: function(args) {
			var modules = args[0];
			var categories = args[1];
			this._moduleStore = this._createModuleStore(modules, categories);

			// make sure that we do not overwrite an explicitely stated value of 'overview'
			var launchableModules = this._getLaunchableModules();
			if (getQuery('overview') === undefined) {
				// disable overview if only one or no module exists
				tools.status('overview', launchableModules.length > 1 && tools.status('overview'));
			} else if (launchableModules.length === 0) {
				tools.status('overview', false);
			}
		},

		_reloadModuleStore: function(args) {
			var modules = args[0];
			var categories = args[1];

			categories.unshift({
				label: _('Favorites'),
				name: _('Favorites'),
				id: '_favorites_',
				priority: Number.POSITIVE_INFINITY
			});

			when(this._moduleStore.query(), lang.hitch(this, function(items) {
				array.forEach(items, function(item) {
					this._moduleStore.remove(item.$id$);
				}, this);

				this._grid.set('categories', categories);
				this._moduleStore.constructor(modules, categories);
			}));
		},

		_tryLoadingModule: function(_module, i) {
			var deferred = new Deferred();
			try {
				require(['umc/modules/' + _module.id], lang.hitch(this, function(baseClass) {
					var module = _module;
					if (typeof baseClass == "function" && tools.inheritsFrom(baseClass.prototype, 'umc.widgets._ModuleMixin')) {
						// add module config class to internal list of available modules
						module = lang.mixin({
							BaseClass: baseClass,
							_orgIndex: i  // save the element's original index
						}, _module);
					}
					deferred.resolve(module);
				}));
			} catch (err) {
				deferred.cancel();
			}
			return deferred;
		},

		_createModuleStore: function(modules, categories) {
			return new Observable(new _ModuleStore(modules, categories));
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
				return item.BaseClass && item.category !== '_favorites_';
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
			//		Get all categories as an array. Each entry has the following properties:
			//		{ id, description }.
			return this._moduleStore.getCategory(id);
		},

		addFavoriteModule: function(/*String*/ id, /*String?*/ flavor) {
			if (!_favoritesDisabled) {
				this._moduleStore.addFavoriteModule(id, flavor);
			}
		},

		setupGui: function() {
			// make sure that we have not build the GUI before
			if (tools.status('setupGui')) {
				return;
			}

			// show the menu bar
			style.set(this._headerRight.domNode, 'display', 'block');

			// save hostname and domainname as status information
			tools.status('domainname', _ucr.domainname);
			tools.status('hostname', _ucr.hostname);
			tools.status('fqdn', _ucr.hostname + '.' + _ucr.domainname);

			// setup menus
			this._setupSettingsMenu();
			this._setupHelpMenu();
			this._setupHostInfoMenu();

			this._setupOverviewPage();
			if (tools.status('overview')) {
				// the checks require an overview site
				this._runChecks();
			}
			this._checkNoModuleAvailable();

			// add the TabContainer to the main BorderContainer
			this._topContainer.addChild(this._tabContainer);

			// set a flag that GUI has been build up
			tools.status('setupGui', true);
			this.onGuiDone();
		},

		_setupSettingsMenu: function() {
			if (!this._settingsMenu) {
				return;
			}
			this._settingsMenu.addChild(new CheckedMenuItem({
				label: _('Tooltips'),
				checked: tools.preferences('tooltips'),
				onClick: function() {
					topic.publish('/umc/actions', 'menu-settings', 'tooltips', this.checked ? 'on' : 'off');
					tools.preferences('tooltips', this.checked);
				}
			}));
			this._settingsMenu.addChild(new CheckedMenuItem({
				label: _('Module help description'),
				checked: tools.preferences('moduleHelpText'),
				onClick: function() {
					topic.publish('/umc/actions', 'menu-settings', 'module-help-text', this.checked ? 'on' : 'off');
					tools.preferences('moduleHelpText', this.checked);
				}
			}));
			this._insertLicenseMenuItems();
		},

		_insertLicenseMenuItems: function() {
			// try to insert license dialog
			if (!this.getModule('udm')) {
				return;
			}

			this._insertSeparatorToSettingsMenu();
			this._insertActivationMenuItem();
			this._settingsMenu.addChild(new MenuItem({
				label: _('Import new license'),
				onClick : lang.hitch(this, '_showLicenseImportDialog')
			}), 0);
			this._settingsMenu.addChild(new MenuItem({
				label: _('License information'),
				onClick : lang.hitch(this, '_showLicenseInformationDialog')
			}), 0);
		},

		_insertActivationMenuItem: function() {
			if (_ucr['uuid/license']) {
				// license has already been activated
				return;
			}

			this._settingsMenu.addChild(new MenuItem({
				label: _('Activation of UCS'),
				onClick: lang.hitch(this, '_showActivationDialog')
			}), 0);
		},

		_insertSeparatorToSettingsMenu: function() {
			var menuHasSeparator = array.some(this._settingsMenu.getChildren(), function(ientry) {
				return tools.inheritsFrom(ientry, 'dijit.MenuSeparator');
			});
			if (!menuHasSeparator) {
				this._settingsMenu.addChild(new MenuSeparator({}), 0);
			}
		},

		_setupHelpMenu: function() {
			if (!this._helpMenu) {
				return;
			}
			this._helpMenu.addChild(new MenuItem({
				label: _('Help'),
				onClick : lang.hitch(this, '_showHelpDialog')
			}));

			this._helpMenu.addChild(new MenuItem({
				label: _('Feedback'),
				onClick : lang.hitch(this, '_showFeedbackPage')
			}));

			this._insertPiwikMenuItem();

			this._helpMenu.addChild(new MenuItem({
				label: _('About UMC'),
				onClick : lang.hitch(this, '_showAboutDialog')
			}));

			this._helpMenu.addChild(new MenuSeparator({}));

			this._helpMenu.addChild(new MenuItem({
				label: _('UCS start site'),
				onClick: function() {
					topic.publish('/umc/actions', 'menu-help', 'ucs-start-site');
					var w = window.open( '/ucs-overview?lang=' + kernel.locale, 'ucs-start-site' );
					w.focus();
				}
			}));

			this._helpMenu.addChild(new MenuItem({
				label: _('Univention Website'),
				onClick: function() {
					topic.publish('/umc/actions', 'menu-help', 'website');
					var w = window.open( _('umcUniventionUrl'), 'univention' );
					w.focus();
				}
			}));
		},

		_insertPiwikMenuItem: function() {
			var isUserAdmin = tools.status('username').toLowerCase() == 'administrator';
			if (!(_hasFFPULicense() && isUserAdmin)) {
				return;
			}
			this._insertSeparatorToSettingsMenu();
			this._helpMenu.addChild(new MenuItem({
				label: _('Usage statistics'),
				onClick: lang.hitch(this, '_showPiwikDialog')
			}));
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
			this._hostInfo.set('label', _('Host: ') + fqdn);
		},

		_switchUMC: function(hostname) {
			topic.publish('/umc/actions', 'host-switch');
			tools.openRemoteSession(hostname);
		},

		_setupOverviewPage: function() {
			if (!tools.status('overview')) {
				// no overview page is being displayed
				// (e.g., system setup in appliance scenario)
				return;
			}

			// the container for all category panes
			// NOTE: We add the icon here in the first tab, otherwise the tab heights
			//	   will not be computed correctly and future tabs will habe display
			//	   problems.
			//     -> This could probably be fixed by calling layout() after adding a new tab!
			this._overviewPage = new Page({
				title: _('umcOverviewTabTitle'),
				//headerText: _('umcOverviewHeader'),
				//iconClass: tools.getIconClass('univention'),
				//helpText: _('umcOverviewHelpText'),
				style: 'margin-top:15px;'
			});
			this._tabContainer.addChild(this._overviewPage);

			this._setupOverviewSearchSidebar();
			this._setupOverviewPane();
		},

		_setupOverviewSearchSidebar: function() {
			// add search widget
			this._searchSidebar = new LiveSearchSidebar({
				style: 'width:150px',
				region: 'left'
			});
			this._overviewPage.addChild(this._searchSidebar);

			this._setupOverviewSearchSidebarCategories();
			this._overviewPage.on('show', lang.hitch(this, '_focusSearchField'));
		},

		_setupOverviewSearchSidebarCategories: function() {
			// set the categories
			var categories = lang.clone(this.getCategories());
			categories.unshift({
				label: _('All'),
				id: '_all_'
			});
			this._searchSidebar.set('categories', categories);
			this._searchSidebar.set('allCategory', categories[0]);
		},

		_focusSearchField: function() {
			if (!has('touch')) {
				setTimeout(lang.hitch(this, function() {
					this._searchSidebar.focus();
				}, 0));
			}
		},

		_setupOverviewPane: function() {
			this._grid = new _OverviewPane({
				'class': 'umcOverviewPane',
				categories: this.getCategories(),
				store: this._moduleStore,
				region: 'center',
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
						return item._isFavorite ? _('Remove from favorites') : _('Add to favorites');
					},
					callback: lang.hitch(this, function(id, item) {
						this._toggleFavoriteModule(item);
					})
				}]
			});
			this._overviewPage.addChild(this._grid);
			this._registerGridEvents();
			this._updateQuery();
		},

		_registerGridEvents: function() {
			this._searchSidebar.on('search', lang.hitch(this, '_updateQuery'));
		},

		_runChecks: function() {
			// run several checks
			this._checkUpdateIsRunning();
			this._checkCertificateValidity();
			this._checkLicense();
			this._checkUpdateAvailable();
			this._checkBrowser();
			this._checkRebootRequired();
			this._checkJoinStatus();
			this._checkShowStartupDialog();
		},

		_checkCertificateValidity: function() {
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
				dialog.warn( _( 'The %s will expire in %d days and should be renewed!', certType, days ) );
			}
		},

		_checkLicense: function() {
			if ( this.getModule( 'udm' ) ) {
				// taken from udm.js
				tools.umcpCommand('udm/license', {}, false).then(lang.hitch(this, function(data) {
					var msg = data.result.message;
					if (msg) {
						dialog.warn(msg);
					}
				}), function() {
					console.warn('WARNING: An error occurred while verifying the license. Ignoring error.');
				});
			}
		},

		_checkUpdateAvailable: function() {
			if (this.getModule('updater') && tools.isTrue(_ucr['update/available'])) {
				var link = this.linkToModule('updater');
				dialog.notify(_( 'An update for UCS is available. Please visit the %s to install the updates.', link));
			}
		},

		_checkUpdateIsRunning: function() {
			if (this.getModule('updater')) {
				tools.umcpCommand('updater/installer/running', {}, false).then(lang.hitch(this, function(data) {
					if (data.result == 'release') {
						this.openModule('updater');
						dialog.alert(_('<p><b>Caution!</b> Currently a release update is performed!</p>') + ' ' +  _('<p>Leave the system up and running until the update is completed!</p>'), _('Release update'));
					}
				}));
			}
		},

		_checkBrowser: function() {
			if (has('ie') < 9 || has('ff') < 4) {
				// supported browsers are FF 3.6 and IE 8
				// they should work with UMC. albeit, they are
				// VERY slow and escpecially IE 8 may take minutes (!)
				// to load a heavy UDM object (on a slow computer at least).
				// IE 8 is also known to cause timeouts when under heavy load
				// (presumably because of many async requests to the server
				// during UDM-Form loading)
				dialog.warn( _( 'Your Browser is outdated and should be updated. You may continue to use Univention Management Console but you may experience performance issues and other problems.' ) );
			}
		},

		_checkForUserRoot: function() {
			if (tools.status('username') == 'root' && tools.isFalse(_ucr['system/setup/showloginmessage'])) {
				var login_as_admin_tag = '<a href="javascript:void(0)" onclick="require(\'umc/app\').relogin(\'Administrator\')">Administrator</a>';
				if (_ucr['server/role'] == 'domaincontroller_slave') {
					dialog.notify( _( 'As %s you do not have access to the App Center. For this you need to log in as %s.', '<strong>root</strong>', login_as_admin_tag ) );
				} else { // master, backup
					dialog.notify( _( 'As %s you have neither access to the domain administration nor to the App Center. For this you need to log in as %s.', '<strong>root</strong>', login_as_admin_tag ) );
				}
			}
		},

		_checkRebootRequired: function() {
			if ( this.getModule('reboot') && tools.isTrue(_ucr['update/reboot/required']) ) {
				var link = this.linkToModule('reboot');
				dialog.notify(_('This system has been updated recently. Please visit the %s and reboot this system to finish the update.', link));
			}
		},

		_checkJoinStatus: function() {
			if (this.getModule('join')) {
				all([
					tools.umcpCommand('join/joined', null, false),
					tools.umcpCommand('join/scripts/query', null, false)
				]).then(
					lang.hitch(this, function(data) {
						var systemJoined = data[0].result;
						var allScriptsConfigured = array.every(data[1].result, function(item) {
							return item.configured;
						});
						var joinModuleLink = this.linkToModule('join');
						if (!systemJoined) {
							// Bug #33389: do not prompt any hint if the system is not joined
							// otherwise we might display this hint if a user runs the appliance
							// setup from an external client.
							//dialog.warn(_('The system has not been joined into a domain so far. Please visit the %s to join the system.', joinModuleLink));
						} else if (!allScriptsConfigured) {
							dialog.notify(_('Not all installed components have been registered. Please visit the %s to register the remaining components.', joinModuleLink));
						}

						if (systemJoined) {
							// Bug #33333: only show the hint for root login if system is joined
							this._checkForUserRoot();
						}
					}), function() {
						console.warn('WARNING: An error occurred while verifying the join state. Ignoring error.');
					}
				);
			}
		},

		_checkNoModuleAvailable: function() {
			var launchableModules = this._getLaunchableModules();
			if (!launchableModules.length) {
				dialog.alert(_('There is no module available for the authenticated user %s.', tools.status('username')));
			}
		},

		_checkShowStartupDialog: function() {
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
		},

		_updateQuery: function() {
			var searchPattern = lang.trim(this._searchSidebar.get('value'));
			var searchQuery = this._searchSidebar.getSearchQuery(searchPattern);
			var searchCategory = this._searchSidebar.get('category');
			this._grid.updateQuery(searchPattern, searchQuery, searchCategory);
		},

		_toggleFavoriteModule: function(module) {
			if (module._isFavorite) {
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

		_setupStaticGui: false,

		_updateScrolling: function() {
			var viewportHeight = win.getBox().h;
			var docHeight = this._topContainer ? domGeometry.getMarginBox(this._topContainer.domNode).h : viewportHeight;
			var scrollStyle = style.get(baseWin.body(), 'overflowY');
			var needsScrolling = Math.abs(viewportHeight - docHeight) > 10;
			var hasScrollbars = (scrollStyle == 'auto' || scrollStyle == 'scroll');
			if (needsScrolling != hasScrollbars) {
				// disable/enable scrollbars
				style.set(baseWin.body(), 'overflowY', needsScrolling ? 'scroll' : 'hidden');
			}
		},

		setupStaticGui: function() {
			// setup everythin that can be set up statically

			// make sure that we have not build the GUI before
			if (this._setupStaticGui) {
				return;
			}

			// show vertical scrollbars only if the viewport size is smaller
			// than 550px (which is our minimal height)
			// this is to avoid having vertical scrollbars when long ComboBoxes open up
			on(baseWin.doc, 'resize', lang.hitch(this, '_updateScrolling'));
			on(kernel.global, 'resize', lang.hitch(this, '_updateScrolling'));

			if (has('touch')) {
				// listen to some more events for updating the scrolling behaviour
				on(kernel.global, 'scroll', lang.hitch(this, '_updateScrolling'));

				// We use specific CSS classes on touch devices (e.g. tablets)
				domClass.add(baseWin.body(), 'umcTouchDevices');

				// make sure that the background cannot be moved unless
				// a virtual keyboard appeared (-> iPad)
				var ignoreTouch = false;
				on(baseWin.doc, 'touchmove', function(evt) {
					if (ignoreTouch) {
						// ignore event
						evt.preventDefault();
					}
				});
				on(baseWin.doc, 'touchend', function(evt) {
					// back to default
					ignoreTouch = false;
				});
				on(baseWin.doc, 'touchstart', function(evt) {
					if (evt.touches.length > 1) {
						// ignore touches with more than 1 finger -> zoom gesture
						ignoreTouch = false;
						return;
					}

					// by default ignore touch unless it happens somewhere in a
					// DOM element that can be scrolled
					ignoreTouch = true;
					var scrollStyle = '';
					for (var node = evt.target; node; node = node.parentNode) {
						try {
							scrollStyle = style.get(node, 'overflowY');
							if (scrollStyle == 'auto' || scrollStyle == 'scroll') {
								ignoreTouch = false;
								break;
							}
						}
						catch (err) {
							// ignore error
						}
					}
				});
			}

			// set up fundamental layout parts...

			// enforce a minimal height of 550px on normal devices
			// and take the viewport height as fixed height on touch devices
			var styleStr = lang.replace('min-height: {0}px;', [550]);
			if (has('touch')) {
				styleStr = lang.replace('height: {0}px;', [Math.max(win.getBox().h, 500)]);
			}
			if (tools.status('width')) {
				styleStr += 'width: ' + tools.status('width') + 'px;';
			}
			this._topContainer = new BorderContainer( {
				'class': 'umcTopContainer',
				gutters: false,
				// force a displayed width if specified
				style: styleStr
			}).placeAt(baseWin.body());

			// container for all modules tabs
			if (tools.status('overview')) {
				this._tabContainer = new TabContainer({
					region: 'center',
					'class': 'umcMainTabContainer'
				});
			} else {
				this._tabContainer = new StackContainer({
					region: 'center',
					'class': 'umcMainTabContainer dijitTabContainer dijitTabContainerTop'
				});
			}

			// register events for closing and focusing
			this._tabContainer.watch('selectedChildWidget', function(name, oldModule, newModule) {
				if (!newModule.moduleID) {
					// this is the overview page, not a module
					topic.publish('/umc/actions', 'overview');
				} else {
					topic.publish('/umc/actions', newModule.moduleID, newModule.moduleFlavor, 'focus');
				}
			});
			aspect.before(this._tabContainer, 'removeChild', function(module) {
				topic.publish('/umc/actions', module.moduleID, module.moduleFlavor, 'close');
			});

			// the header
			var header = new ContainerWidget({
				'class': 'umcHeader',
				region: 'top'
			});
			this._topContainer.addChild( header );

			this._headerRight = new ContainerWidget({
				'class': 'umcHeaderRight',
				style: 'float: right; display: none;'
			});
			header.addChild(this._headerRight);

			var _addToHeader = lang.hitch(this, function(tooltipLabel, button) {
				new UMCTooltip({
					label: tooltipLabel,
					connectId: [ button.domNode ]
				});
				this._headerRight.addChild(button);
			});

			if (tools.status('displayUsername')) {
				// the host info and menu
				this._hostMenu = new Menu({});
				this._hostInfo = new DropDownButton({
					id: 'umcMenuHost',
					label: '',
					disabled: true,
					dropDown: this._hostMenu
				});
				this._headerRight.addChild(this._hostInfo);

				this._headerRight.addChild(new Text({
					'class': 'umcHeaderSeparator'
				}));

				// display the username
				this._headerRight.addChild(new Text({
					id: 'umcMenuUsername',
					'class': 'umcHeaderText',
					content: _('umcUserInfo', {
						username: tools.status('username')
					})
				}));

				this._headerRight.addChild(new Text({
					'class': 'umcHeaderSeparator'
				}));

				// the settings context menu
				this._settingsMenu = new Menu({});
				_addToHeader(_('Settings'), new DropDownButton({
					id: 'umcMenuSettings',
					iconClass: 'icon24-umc-menu-settings',
					dropDown: this._settingsMenu
				}));

				// the help context menu
				this._helpMenu = new Menu({});
				_addToHeader(_('Help'), new DropDownButton({
					id: 'umcMenuHelp',
					iconClass: 'icon24-umc-menu-help',
					dropDown: this._helpMenu
				}));

				// the notification button
				_addToHeader(_('Notifications'), new Button({
					id: 'umcMenuNotifications',
					iconClass: 'icon24-umc-menu-notifications',
					onClick: lang.hitch(dialog, 'toggleNotifications')
				}));

				// the logout button
				_addToHeader(_('Logout'), new Button({
					id: 'umcMenuLogout',
					iconClass: 'icon24-umc-menu-logout',
					onClick: lang.hitch(this, function() {
						this.relogin();
					})
				}));
			}

			// put everything together
			this._topContainer.startup();
			this._updateScrolling();

			// subscribe to requests for opening modules and closing/focusing tabs
			topic.subscribe('/umc/modules/open', lang.hitch(this, 'openModule'));
			topic.subscribe('/umc/tabs/close', lang.hitch(this, 'closeTab'));
			topic.subscribe('/umc/tabs/focus', lang.hitch(this, 'focusTab'));
			topic.subscribe('/umc/license/activation', lang.hitch(this, '_showActivationDialog'));

			this._setupStaticGui = true;
		},

		_showLicenseImportDialog: function() {
			topic.publish('/umc/actions', 'menu-settings', 'license-import');
			require(['umc/modules/udm/LicenseImportDialog'], function(LicenseImportDialog) {
				var dlg = new LicenseImportDialog();
				dlg.show();
			});
		},

		_showLicenseInformationDialog: function() {
			topic.publish('/umc/actions', 'menu-settings', 'license');
			require(['umc/modules/udm/LicenseDialog'], function(LicenseDialog) {
				var dlg = new LicenseDialog();
				dlg.show();
			});
		},

		_showActivationDialog: function() {
			topic.publish('/umc/actions', 'menu-settings', 'activation');

			/** The following two checks are only for if this dialogue is opened via topic.publish() **/
			if (_ucr['uuid/license']) {
				dialog.alert(_('The license has already been activated.'));
				return;
			}
			if (!this.getModule('udm')) {
				dialog.alert(_('Activation is not possible. Please login as Administrator on the DC master.'));
				return;
			}

			var _reopenActivationDialog = lang.hitch(this, function(_deferred) {
				if (!_deferred) {
					_deferred = new Deferred();
				}
				var _emailWidget = registry.byId('umc_app_activation_email');
				if (!_emailWidget) {
					this._showActivationDialog();
					_deferred.resolve();
				} else {
					// the previous dialog has not been destroyed completely...
					// try again after a small timeout
					setTimeout(lang.hitch(this, _reopenActivationDialog, _deferred), 200);
				}
				return _deferred;
			});

			var confirmDeferred = dialog.templateDialog('umc/app', 'activation.' + _getLang()  + '.html', {
				path: require.toUrl('umc/app'),
				leaveFieldFreeDisplay: 'none',
				version: tools.status('ucsVersion').split('-')[0]
			}, _('Activation of UCS'), [{
				name: 'cancel',
				label: _('Cancel')
			}, {
				name: 'activate',
				label: _('Activate'),
				'default': true
			}]);

			confirmDeferred.then(lang.hitch(this, function(response) {
				if (response != 'activate') {
					return;
				}

				var emailWidget = registry.byId('umc_app_activation_email');
				if (!emailWidget.isValid()) {
					_reopenActivationDialog().then(function() {
						dialog.alert(_('Please enter a valid email address!'));
					});
				} else {
					tools.umcpCommand('udm/request_new_license', {
						email: emailWidget.get('value')
					}, false).then(lang.hitch(this, function() {
						this._showLicenseImportDialog();
					}), lang.hitch(this, function(error) {
						_reopenActivationDialog().then(function() {
							tools.handleErrorStatus(error.response);
						});
					}));
				}
			}));
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
			} );
		},

		_showHelpDialog: function() {
			topic.publish('/umc/actions', 'menu-help', 'help');
			dialog.templateDialog('umc/app', 'help.' + _getLang()  + '.html', {
				path: require.toUrl('umc/app')
			}, _('Help'), _('Close'));
		},

		_showPiwikDialog: function() {
			topic.publish('/umc/actions', 'menu-help', 'piwik');
			dialog.templateDialog('umc/app', 'feedback.' + _getLang()  + '.html', {
				path: require.toUrl('umc/app'),
				hardwareStatisticsCheckboxDisplay: 'none',
				version: tools.status('ucsVersion').split('-')[0]
			}, _('Usage statistics'), _('Close'));
		},

		_showFeedbackPage: function() {
			topic.publish('/umc/actions', 'menu-help', 'feedback');
			var url = _('umcFeedbackUrl') + '?umc=' + this._tabContainer.get('selectedChildWidget').title;
			var w = window.open(url, 'umcFeedback');
			w.focus();
		},

		_disablePiwik: function(disable) {
			topic.publish('/umc/piwik/disable', disable);
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
						window.location.reload();
					} else {
						window.location.search = 'username=' + username;
					}
				})
			}]);
		},

		linkToModule: function(/*String*/ moduleId, /*String?*/ moduleFlavor, /*String?*/ linkName) {
			var module = this.getModule(moduleId, moduleFlavor);
			if (!module) {
				return null;
			}

			var link = '<a href="javascript:void(0)" onclick="require(\'umc/app\').openModule(${moduleLink})">${linkName}</a>';
			var moduleLink = moduleFlavor ? "'${0}', '${1}'" : "'${0}'";
			moduleLink = string.substitute(moduleLink, [moduleId, moduleFlavor]);

			linkName = string.substitute(linkName || _('"${moduleName}" module'), { moduleName: module.name });
			return string.substitute(link, {moduleLink: moduleLink, linkName: linkName});
		},

		onGuiDone: function() {
			// event stub
		}
	});
	return new _App();
});
