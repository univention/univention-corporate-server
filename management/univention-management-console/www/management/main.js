/*
 * Copyright 2011-2021 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global umc,define,require,console,window,setTimeout,dojo*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/on/debounce",
	"dojo/on",
	"dojo/aspect",
	"dojo/has",
	"dojo/Evented",
	"dojo/Deferred",
	"dojo/promise/all",
	"dojo/cookie",
	"dojo/topic",
	"dojo/io-query",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dojo/dom",
	"dojo/dom-class",
	"dojo/dom-construct",
	"put-selector/put",
	"dojo/hash",
	"dojox/html/styles",
	"dojox/html/entities",
	"dojox/gfx",
	"umc/tools",
	"login",
	"umc/dialog",
	"umc/dialog/NotificationSnackbar",
	"umc/store",
	"dijit/Tooltip",
	"dijit/layout/StackContainer",
	"umc/menu",
	"umc/menu/Button",
	"umc/widgets/TabController",
	"umc/widgets/LiveSearch",
	"umc/widgets/GalleryPane",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/Button",
	"umc/widgets/ToggleButton",
	"umc/widgets/Text",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/NotificationsButton",
	"umc/widgets/MobileTabsButton",
	"umc/i18n/tools",
	"umc/i18n!management",
	"dojo/sniff" // has("ie"), has("ff")
], function(declare, lang, kernel, array, baseWin, onDebounce, on, aspect, has, Evented, Deferred, all, cookie, topic,
		ioQuery, Memory, Observable, dom, domClass, domConstruct, put, dojoHash, styles, entities, gfx, tools, login,
		dialog, NotificationSnackbar, store, Tooltip, StackContainer, menu, MenuButton,	TabController, LiveSearch,
		GalleryPane, ContainerWidget, Page, Form, Button, ToggleButton, Text, ConfirmDialog, NotificationsButton,
		MobileTabsButton, i18nTools, _
) {
	var _favoritesDisabled = false;
	var _initialHash = decodeURIComponent(dojoHash());
	var _overviewVisible = true;
	var _menuVisible = true;

	// helper function for sorting, sort indices with priority < 0 to be at the end
	var _cmpPriority = function(x, y) {
		if (y.priority === x.priority) {
			return x._orgIndex - y._orgIndex;
		}
		return y.priority - x.priority;
	};

	// "short" cut (well at least more verbose) for checking for favorite module
	var isFavorite = function(mod) {
		return array.indexOf(mod.categories, '_favorites_') >= 0;
	};

	var _OverviewPane = declare([GalleryPane], {
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

			this.contrastMap = {};
			this.categories.forEach(lang.hitch(this, function(category) {
				var contrastLight = umc.tools.contrast(category.color, '#fff');
				var contrastDark  = umc.tools.contrast(category.color, 'rgba(0, 0, 0, 0.87)');
				this.contrastMap[category.id] = contrastDark > contrastLight ? 'contrastDark' : 'contrastLight';
			}));
		},

		getIconClass: function(item) {
			if (item.icon) {
				var icon;
				if (/\.svg$/.test(item.icon)) {
					icon = item.icon.replace(/\.svg$/, '');
					return tools.getIconClass(icon, 'scalable', '', 'background-size: contain;');
				}

				// for backwards compatibility we need to support png
				icon = lang.replace('{icon}.png', item);
				return tools.getIconClass(icon, 50);
			}
			return '';
		},

		_createFavoriteIcon: function(category, parentNode) {
			var node = domConstruct.create('div', {
				'class': 'umcFavoriteIconDefault'
			}, parentNode);
			var surface = gfx.createSurface(node, 10, 10);
			surface.createPolyline([
				{x: 0, y: 0},
				{x: 0, y: 10},
				{x: 5, y: 5.6},
				{x: 10, y: 10},
				{x: 10, y: 0}
			]).setFill(category.color);
		},

		renderRow: function(item, options) {
			var div = this.inherited(arguments);
			var category_for_color = item.category_for_color;
			var className = lang.replace('umcGalleryCategory-{0}', [category_for_color]);
			domClass.add(div.firstElementChild, className);
			domClass.add(div.firstElementChild, lang.replace('umcGalleryCategory--{0}', [this.contrastMap[item.category_for_color]]));
			if (isFavorite(item)) {
				var cat = require('umc/app').getCategory(category_for_color);
				if (cat) {
					this._createFavoriteIcon(cat, div.firstElementChild);
				}
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
					(searchQuery.test(obj) && obj.category !== '_favorites_');
				var matchesCategory = true;
				if (!allCategories) {
					matchesCategory = obj.category == category.id;
				}
				else if (obj.category === '_favorites_') {
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

		_isNotShallowCopy: function(category){
			// to get the origin color of the category, we will ignore each
			// category that starts && ends with an underscore _
			// e.g. returns false for _favorites_ category
			var re = /^_.*_$/;
			return !re.test(category);
		},

		_isNotFavorites: function(cat) {
			return cat !== '_favorites_';
		},

		_createModuleItem: function(_item, categoryID) {
			// we need a unique ID for the store
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

			// by convention a link element has an url
			item.is_link = Boolean(item.url);
			item.is_shallow_copy = !this._isNotShallowCopy(item.category);
			item.category_for_color = item.category;
			if (item.is_shallow_copy && item.categories.length > 1) {
				item.category_for_color = array.filter(item.categories, this._isNotShallowCopy)[0] ||
					array.filter(item.categories, this._isNotFavorites)[0];
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
				flavor: flavor || null,
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

			var favoritesButton = this.getCategory('_favorites_')._button;
			domClass.toggle(favoritesButton.domNode, 'favoritesHidden', (this.getModules('_favorites_').length === 0));

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
			var favoritesButton = this.getCategory('_favorites_')._button;
			domClass.toggle(favoritesButton.domNode, 'favoritesHidden', (this.getModules('_favorites_').length === 0));
			// save settings
			this._saveFavorites();
		}
	});

	topic.subscribe('/umc/started', function() {

		var checkCertificateValidity = function() {
			var hostCert = parseInt(tools.status('ssl/validity/host'), 10);
			var rootCert = parseInt(tools.status('ssl/validity/root'), 10);
			var warning = parseInt(tools.status('ssl/validity/warning'), 10);
			var certExp = rootCert;
			var certType = _('SSL root certificate');
			if (rootCert >= hostCert) {
				certExp = hostCert;
				certType = _('SSL host certificate');
			}
			var today = new Date().getTime() / 1000 / 60 / 60 / 24; // now in days
			var days = certExp - today;
			if (days <= warning) {
				dialog.warn(_('The %(certificate)s will expire in %(days)d days and should be renewed!', {certificate: certType, days: days}));
			}
		};

		var summit2021DialogWasShown = true;
		var showSummit2021Dialog = function() {
			var endOfSummit = new Date(2021, 0, 28, 0, 0, 0);
			var summitHasPassed = endOfSummit < new Date();
			var isUserAdmin = app.getModule('updater') || app.getModule('schoolrooms');
			var dontShowDialog = !tools.status('has_free_license') || summitHasPassed || !isUserAdmin || cookie('hideSummit2021Dialog');
			if (dontShowDialog) {
				summit2021DialogWasShown = false;
				return;
			}

			var title = '' +
				'<div>' +
					'<p class="umcSummit2021Dialog__header-text">' +
						'Univention Summit 2021' +
					'</p>' +
				'</div>';

			var message_base = '' +
				'<div class="umcSummit2021Message">' +
					'<div class="umcSummit2021Message__messageWrapper">' +
						'{0}' +
						'<ul>' +
							'<li>{1}</li>' +
							'<li>{2}</li>' +
							'<li>{3}</li>' +
							'<li>{4}</li>' +
							'<li>{5}</li>' +
							'<li>{6}</li>' +
							'<li>{7}</li>' +
						'</ul>' +
						'<a class="umcSummit2021Message__link" href="{8}" target="_blank">{9}</a>' +
					'</div>' +
					'<div class="umcSummit2021Message__image">' +
					'</div>' +
				'</div>';
			var message_de = lang.replace(message_base, [
				title,
				'Virtual Venue am 28. Januar 2021',
				'500 Teilnehmende',
				'25 Aussteller & Sponsoren',
				'Keynotes, Workshops, Round Tables & Praxisvorträge',
				'Roadmap: UCS 5 und UCS@school 5',
				'Digitale Souveränität: Phoenix, Gaia X und SCS',
				'Digitale Bildung: Bildungs-Cloud, Schulportale und IT-Lösungen',
				'https://www.univention-summit.de/?pk_campaign=Summit21-UMC-Popup',
				'Jetzt registrieren'
			]);

			var message_en = lang.replace(message_base, [
				title,
				'Virtual Venue on January 28, 2021',
				'500 Attendees',
				'25 Exhibitors & Sponsors',
				'Keynotes, Workshops, Round Tables & Best Practices',
				'Roadmap: UCS 5 and UCS@school 5',
				'Digital Sovereignty: Phoenix, Gaia X and SCS',
				'Digital Education: Educational Cloud, School Portals and IT Solutions',
				'https://www.univention-summit.com/?pk_campaign=Summit21-UMC-Popup',
				'Register now'
			]);

			var isDE = (kernel.locale.toLowerCase().indexOf('de') === 0);
			var message = isDE ? message_de : message_en;

			var options = [{
				'label': 'OK',
				'default': true
			}];

			// preload the image and then show dialog
			var img = new Image();
			on(img, ['load', 'error'], function() {
				img = null; // garbage collect the img

				var dialog = new ConfirmDialog({
					'class': 'umcSummit2021Dialog',
					title: title,
					message: message,
					options: options,
				});
				on(dialog, 'confirm', function() {
					var nowInTwoWeeks = new Date(Date.now() + (1000 * 60 * 60 * 24 * 14));
					var expires = nowInTwoWeeks < endOfSummit ? nowInTwoWeeks : endOfSummit;
					cookie('hideSummit2021Dialog', 'true', {expires: expires.toUTCString()});
					dialog.close();
				});
				dialog.show();
			});
			img.src = '/univention/management/univention-summit-2021.svg';
		};

		var showSummit2021Notification = function() {
			if (summit2021DialogWasShown) {
				return;
			}

			var endOfSummit = new Date(2021, 0, 28, 0, 0, 0);
			var summitHasPassed = endOfSummit < new Date();
			var isUserAdmin = app.getModule('updater') || app.getModule('schoolrooms');
			var dontShowNotification = !tools.status('has_free_license') || summitHasPassed || !isUserAdmin || cookie('hideSummit2021Notification');
			if (dontShowNotification) {
				return;
			}

			var isDE = (kernel.locale.toLowerCase().indexOf('de') === 0);
			var message_de = '<a href="https://www.univention-summit.de/?pk_campaign=Summit20-UMC-Nachricht" target="_blank">Univention Summit 2021</a> - Anwender, OS-Hersteller & Univention treffen und alles zu UCS 5 & Best Practices erfahren.';
			var message_en = '<a href="https://www.univention-summit.com/?pk_campaign=Summit20-UMC-Nachricht" target="_blank">Univention Summit 2021</a> - Meet users, OS vendors & Univention and learn all about UCS 5 & Best Practices. ';
			var message = isDE ? message_de : message_en;
			dialog.notify(message).then(function(notification) {
				on(notification, 'remove', function() {
					var nowInTwoWeeks = new Date(Date.now() + (1000 * 60 * 60 * 24 * 14));
					var expires = nowInTwoWeeks < endOfSummit ? nowInTwoWeeks : endOfSummit;
					cookie('hideSummit2021Notification', 'true', {expires: expires.toUTCString()});
				});
			});
		};

		var showAmbassadorNotification = function() {
			var endOfAmbassadorProgram = new Date(2019, 7, 14, 0, 0, 0);
			var ambassadorProgramHasPassed = endOfAmbassadorProgram < new Date();
			var isUserAdmin = app.getModule('updater') || app.getModule('schoolrooms');
			var dontShowNotification = !tools.status('has_free_license') || ambassadorProgramHasPassed || !isUserAdmin || cookie('hideAmbassadorNotification');
			if (dontShowNotification) {
				return;
			}

			var message = 'Write a comment, a short review, or a tutorial about UCS and collect valuable bonus points as a UCS Ambassador. More information: <a href="http://bit.ly/UCS_Ambassador_Program" target="_blank" rel="noopener">UCS Ambassador Program</a>';
			var title = 'UCS Ambassador Program';
			switch (i18nTools.defaultLang().substring(0, 2)) {
				case 'de':
					message = 'Jetzt Kommentar, kurzes Review oder Tutorial zu UCS schreiben und als UCS Ambassador wertvolle Bonuspunkte sammeln! Mehr Infos: <a href="http://bit.ly/UCS_Ambassador" target="_blank" rel="noopener">UCS Ambassador Programm</a>'; 
					title = 'UCS Ambassador Programm';
					break;
				case 'fr':
					message = 'Écrivez un commentaire, une courte critique ou un tutoriel sur UCS et accumulez de précieux points en prime en tant qu\'ambassadeur de UCS! Plus d\'info: <a href="http://bit.ly/UCS_Ambassador_Program_France" target="_blank" rel="noopener">Programme des ambassadeurs de UCS</a>';
					title = 'Programme des ambassadeurs de UCS';
					break;
			}

			dialog.notify(message, title, false).then(function(notification) {
				on(notification, 'remove', function() {
					// make sure that the cookie does not expire too early
					var expires = new Date(endOfAmbassadorProgram);
					expires.setDate(expires.getDate() + 7);
					cookie('hideAmbassadorNotification', 'true', {expires: expires.toUTCString()});
				});
			});
		};

		// run several checks
		checkCertificateValidity();
		showSummit2021Dialog();
		showSummit2021Notification();
		showAmbassadorNotification();
	});

	var UmcHeader = declare([ContainerWidget], {

		// top tap bar (handed over upon instantiation)
		_tabController: null,
		_tabContainer: null,

		_headerRight: null,
		_hostInfo: null,
		_hostMenu: null,

		_resize: function() {
			this._updateTabsVisibility();
		},

		setupGui: function() {
			// show the menu bar
			this.setupHeader();
			this.setupHelpMenu();
			this.setupPiwikMenu();

			on(window, onDebounce('resize', 200), lang.hitch(this, function() {
				this._resize();
			}));
		},

		setupHeader: function() {
			this._headerRight = new ContainerWidget({
				'class': 'umcHeaderRight'
			});

			if (_overviewVisible) {
				this.setupBackToOverview();
			}
			this._setupModuleTabs();

			this.addChild(this._headerRight);
			if (_overviewVisible) {
				this.setupSearchField();
			}
			this._headerRight.addChild(new NotificationsButton({}));
			if (_menuVisible) {
				this._headerRight.addChild(new MenuButton({}));
			}
		},

		mobileTabsView: false,
		_setMobileTabsViewAttr: function(isTrue) {
			tools.toggleVisibility(this._tabController, !isTrue);
			tools.toggleVisibility(this._headerStretch, isTrue);
			tools.toggleVisibility(this._mobileTabsButton, isTrue);
			this._set('mobileTabsView', isTrue);
		},

		_setupModuleTabs: function() {
			this._mobileTabsButton = new MobileTabsButton({});
			this._headerRight.addChild(this._mobileTabsButton);
			var mobileTabsContainer = this._mobileTabsButton.mobileTabsContainer;

			var aspectHandlesMap = {};
			this._tabController.on('addChild', lang.hitch(this, function(module) {
				if (!module.isOverview) {
					var tab = put(`div.umcMobileTab#umcMobileTab_${module.id}`);
					on(tab, 'click', lang.hitch(this, function(evt) {
						evt.stopImmediatePropagation();
						this._tabContainer.selectChild(module);
						this._mobileTabsButton.set('checked', false);
					}));
					var labelNode = put(tab, 'div.umcMobileTab__label', module.title);
					if (module.closable) {
						var closeButton = Button.simpleIconButtonNode('x', 'umcMobileTab__closeButton');
						on(closeButton, 'click', lang.hitch(this, function(evt) {
							evt.stopImmediatePropagation();
							module.closeModule();
							if (mobileTabsContainer.children.length === 0 || !this._areTabsVisible()) {
								this._mobileTabsButton.set('checked', false);
							}
						}));
						put(tab, closeButton);
					}
					put(mobileTabsContainer, tab);

					this._updateTabsVisibility();

					aspectHandlesMap[module.id] = aspect.after(module, '_setTitleAttr', lang.hitch(this, function(label) {
						labelNode.innerHTML = label;
						this._updateTabsVisibility();
					}), true);
				}
			}));
			this._tabController.on('removeChild', lang.hitch(this, function(module) {
				aspectHandlesMap[module.id].remove();
				delete aspectHandlesMap[module.id];

				var node = document.getElementById(`umcMobileTab_${module.id}`);
				if (node) {
					node.remove();
				}
				this._updateTabsVisibility();
			}));

			this.addChild(this._tabController);
			domClass.toggle(this._tabController.domNode, 'umcMainTabController--overviewless', !_overviewVisible);
			this._headerStretch = put(this.domNode, 'div.umcHeaderStretch.dijitDisplayNone');
		},

		_getNumOfTabs: function() {
			return this._tabContainer.getChildren().filter(function(tab) {
				return !tab.isOverview;
			}).length;
		},

		_areTabsVisible: function() {
			return _overviewVisible || this._getNumOfTabs() >= 2;
		},

		_updateTabsVisibility: function() {
			var areTabsVisible = this._areTabsVisible();
			// update mobile tabs
			this._mobileTabsButton.counterNode.innerHTML = this._getNumOfTabs();
			this.set('mobileTabsView', false);
			if (areTabsVisible) {
				window.requestAnimationFrame(lang.hitch(this, function() {
					this.set('mobileTabsView', this._tabController.domNode.scrollWidth > this._tabController.domNode.clientWidth);
				}));
			}
			tools.toggleVisibility(this._tabController, areTabsVisible);
		},

		setupSearchField: function() {
			this._search = new LiveSearch({
				searchLabel: _('Search'),
				'class': 'umcModuleSearch',
				collapsible: false,
				disabled: true
			});
			var searchToggleButton = new ToggleButton({
				iconClass: 'search',
				'class': 'ucsIconButton umcModuleSearchToggleButton'
			});

			on(this._search, 'keyup', lang.hitch(this, function(evt) {
				if (evt.key === 'Escape') {
					searchToggleButton.set('checked', false);
					setTimeout(function() {
						searchToggleButton.focus();
					}, 0);
				}
			}));
			searchToggleButton.watch('checked', lang.hitch(this, function(_attr, _oldChecked, checked) {
				domClass.toggle(this._search.domNode, 'umcModuleSearch--open', checked);
				if (checked) {
					this.switchToOverview();
					setTimeout(lang.hitch(this, function() {
						this._search.focus();
					}, 0));
				} else {
					this._search.set('value', '');
					this._search.search();
				}
				this._search.set('disabled', !checked);
			}));
			this._tabContainer.watch('selectedChildWidget', function(_name, _oldModule, newModule) {
				if (newModule.id !== 'umcOverviewPage') {
					searchToggleButton.set('checked', false);
				}
			});

			this._headerRight.addChild(searchToggleButton);
			this._headerRight.addChild(this._search);
		},

		setupBackToOverview: function() {
			this._backToOverviewButton = new Button({
				'class': 'umcBackToOverviewButton ucsIconButton',
				iconClass: 'home',
				onClick: function() {
					require('umc/app').switchToOverview();
				}
			});
			this.addChild(this._backToOverviewButton);
		},

		setupHelpMenu: function() {
			// the help context menu
			menu.addSeparator({
				parentMenuId: 'umcMenuHelp',
				priority: 50
			});

			menu.addEntry({
				parentMenuId: 'umcMenuHelp',
				label: _('Documentation and Support'),
				priority: 40,
				onClick: lang.hitch(this, 'showPageDialog', 'HelpPage', 'help', null, null)
			});

			menu.addEntry({
				parentMenuId: 'umcMenuHelp',
				label: _('About UMC'),
				priority: 30,
				onClick: lang.hitch(this, 'showPageDialog', 'AboutPage!', 'about', null, null)
			});
		},

		setupPiwikMenu: function() {
			var isUserAdmin = tools.status('username').toLowerCase() === 'administrator';
			if (!(tools.status('hasFreeLicense') && isUserAdmin)) {
				return;
			}
			menu.addEntry({
				parentMenuId: 'umcMenuHelp',
				label: _('Usage statistics'),
				priority: 20,
				onClick: lang.hitch(this, 'showPageDialog', 'FeedbackPage', 'feedback', null, null)
			});
		},

		showPageDialog: function(_PageRef, key, buttonsConf, additionCssClasses) {
			// publish action + set default values
			topic.publish('/umc/actions', 'menu', 'help',  key);
			additionCssClasses = additionCssClasses || '';
			buttonsConf = buttonsConf || [{
				name: 'submit',
				'default': true,
				label: _('Close')
			}];

			// require given Page reference and display the dialog
			var deferred = new Deferred();
			require(["management/widgets/" + _PageRef], lang.hitch(this, function(_pageConf) {
				// prepare dict
				var pageConf = lang.mixin({
					'class': ''
				}, _pageConf);
				pageConf['class'] += ' ' + additionCssClasses;

				// create a new form to render the widgets
				var form = new Form(lang.mixin({
					region: 'main'
				}, pageConf));

				// create a page containing additional methods validate(),
				// _getValueAttr(), on() and onSubmit() in order to fake Form
				// behavior for umc/dialog::confirmForm()
				var page = new Page(pageConf);
				page = lang.delegate(page, {
					validate: lang.hitch(form, 'validate'),
					_getValueAttr: lang.hitch(form, '_getValueAttr'),
					// fake call to on('submit', function)
					_callbacks: null,
					on: function(type, cb) {
						if (type === 'submit') {
							this._callbacks = this._callbacks || [];
							this._callbacks.push(cb);
						}
					},
					onSubmit: function(values) {
						array.forEach(this._callbacks, function(icb) {
							icb(values);
						});
					}
				});
				form.on('submit', lang.hitch(page, 'onSubmit'));

				// add elements to page
				page.addChild(form);
				page.addChild(new Text({
					'class': 'umcPageIcon',
					region: 'nav'
				}));

				// show dialog
				dialog.confirmForm({
					form: page,
					title: pageConf.headerText,
					'class': 'umcLargeDialog umcAppDialog',
					buttons: buttonsConf
				}).then(function(response) {
					deferred.resolve(response);
				}, function() {
					deferred.resolve(null);
				});
			}));
			return deferred;
		}
	});

	var TabButton = declare([TabController.TabButton], {
		//// overwrites
		cssStateNodes: {
			closeNode: 'umcModuleTab__closeButton'
		},


		//// lifecycle
		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcModuleTab');

			var backgroundNode = put('div.umcModuleTab__background');
			domConstruct.place(backgroundNode, this.domNode, 'first');
			var nodeLeft = domConstruct.toDom('<svg class="umcModuleTab__background__svg umcModuleTab__background__svg--left" viewBox="0 0 100 100"><path d="M0,100 L100,100 L100,0 Q 85 85 0 100 z" /></svg>');
			domConstruct.place(nodeLeft, backgroundNode);

			var nodeRight = domConstruct.toDom('<svg class="umcModuleTab__background__svg umcModuleTab__background__svg--right" viewBox="0 0 100 100"><path d="M0,0 Q 15 85 100 100  L 0,100 z" /></svg>');
			domConstruct.place(nodeRight, backgroundNode);

			var closeButtonNode = Button.simpleIconButtonNode('x', 'umcModuleTab__closeButton');
			put(this.closeNode, '+', closeButtonNode);
			put(this.closeNode, '!');
			this.closeNode = closeButtonNode;
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
			//		* overview (Boolean): Specifies whether or not the overview of available modules
			//		                      and the search is displayed or not. (detault: true)
			//		* menu (Boolean): Specifies whether or not the hamburger menu is displayed. (default: true)

			// username will be overridden by final authenticated username
			tools.status('username', props.username || tools.status('username'));
			// password has been given in the query string... in this case we may cache it, as well
			tools.status('password', props.password);

			if (props.overview !== undefined) {
				_overviewVisible = tools.isTrue(props.overview);
			}
			
			if (props.menu !== undefined) {
				_menuVisible = tools.isTrue(props.menu);
			}

			login.onInitialLogin(lang.hitch(this, '_authenticated'));
		},

		_authenticated: function() {
			this.setupStaticGui();
			this.load();
		},

		_tabContainer: null,
		_topContainer: null,
		_topContainerGeneralCSSClasses: [],
		_topContainerModuleSpecificCSSClasses: [],
		_topContainerModuleSpecificCSSClassesWatchHandler: null,
		_overviewPage: null,
		_categoriesContainer: null,
		_setupStaticGui: false,
		_moduleStore: null,
		_categories: [],
		_loaded: false,
		_lastCategory: null,

		setupStaticGui: function() {
			// setup everything that can be set up statically

			// make sure that we have not build the GUI before
			if (this._setupStaticGui) {
				return;
			}

			if (has('touch')) {
				this.setupTouchDevices();
			}

			// set up fundamental layout parts...

			this._topContainer = new ContainerWidget({
				id: 'umcTopContainer',
				domNode: dom.byId('umcTopContainer'),
				containerNode: dom.byId('umcTopContainer'),
				'class': 'umcTopContainer'
			});

			// module (and overview) container
			this._tabContainer = new StackContainer({
				'class': 'umcMainTabContainer dijitTabContainer dijitTabContainerTop'
			});

			// the tab bar
			this._tabController = new TabController({
				'class': 'umcMainTabController',
				containerId: this._tabContainer.id,
				buttonWidget: TabButton,
				buttonWidgetCloseClass: 'umcModuleTab__closeButton'
			});

			// the header
			this._header = new UmcHeader({
				id: 'umcHeader',
				'class': 'umcHeader umcHeader--umc',
				_tabController: this._tabController,
				_tabContainer: this._tabContainer,
				switchToOverview: lang.hitch(this, 'switchToOverview')
			});

			this.registerTabSwitchHandling();

			// put everything together
			this._topContainer.addChild(this._header);
			this._topContainer.addChild(this._tabContainer);
			this._topContainer.addChild(new NotificationSnackbar({}));
			this._topContainer.startup();

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
				deferred.resolve(true);
				topic.publish('/umc/started');
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
				this._updateTopContainerCSSClasses(oldModule, newModule);

				if (!newModule.moduleID) {
					// this is the overview page, not a module
					topic.publish('/umc/actions', 'overview');
				} else {
					topic.publish('/umc/actions', newModule.moduleID, newModule.moduleFlavor, 'focus');
				}
				var overviewShown = (newModule === this._overviewPage);
				domClass.toggle(baseWin.body(), 'umcOverviewShown', overviewShown);
				domClass.toggle(baseWin.body(), 'umcOverviewNotShown', !overviewShown);
				if (newModule.selectedChildWidget && newModule.selectedChildWidget._onShow) {
					newModule.selectedChildWidget._onShow();
				}

				if (oldModule) {
					var mobileTab = dojo.byId(`umcMobileTab_${oldModule.id}`);
					if (mobileTab) {
						domClass.remove(mobileTab, 'umcMobileTab--selected');
					}
				}
				if (newModule) {
					var mobileTab = dojo.byId(`umcMobileTab_${newModule.id}`);
					if (mobileTab) {
						domClass.add(mobileTab, 'umcMobileTab--selected');
					}
				}
			}));
			aspect.before(this._tabContainer, 'removeChild', lang.hitch(this, function(module) {
				this._updateNumOfTabs(-1);
				topic.publish('/umc/actions', module.moduleID, module.moduleFlavor, 'close');

				if (module === this._tabContainer.get('selectedChildWidget')) {
					if (array.indexOf(this._tabContainer.getChildren(), this._lastSelectedChild) !== -1) {
						this._tabContainer.selectChild(this._lastSelectedChild);
					} else {
						this.switchToOverview();
					}
				}
			}));
		},

		_updateTopContainerCSSClasses: function(oldModule, newModule) {
			// remove previously added css classes; cleanup
			domClass.remove(this._topContainer.domNode, this._topContainerGeneralCSSClasses);
			this._topContainerGeneralCSSClasses = [];

			if (this._topContainerModuleSpecificCSSClassesWatchHandler) {
				this._topContainerModuleSpecificCSSClassesWatchHandler.remove();
				this._topContainerModuleSpecificCSSClassesWatchHandler = null;
			}

			var cssClass;

			// add css class for category color of open module
			if (lang.exists('categoryColor', newModule)) {
				cssClass = lang.replace('umcTopContainer--categoryColor-{categoryColor}', newModule);
				this._topContainerGeneralCSSClasses.push(cssClass);
			}

			// add css class for open module id and flavor
			cssClass = newModule.isOverview ? 'overview' : newModule.moduleID;
			cssClass = lang.replace('umcTopContainer--layout-{0}', [cssClass]);
			this._topContainerGeneralCSSClasses.push(cssClass);

			if (lang.exists('moduleFlavor', newModule)) {
				cssClass = lang.replace('{cssClass}-{moduleFlavor}', {
					cssClass: cssClass,
					moduleFlavor: newModule.moduleFlavor.replace(/[^a-zA-Z0-9\-]/g, '-')
				});
				this._topContainerGeneralCSSClasses.push(cssClass);
			}

			domClass.add(this._topContainer.domNode, this._topContainerGeneralCSSClasses);

			// add css classes for module specific pages
			this._removeModuleSpecificCSSClasses();
			if (newModule.selectablePagesToLayoutMapping) {
				this._addModuleSpecificCSSClasses(newModule);
				this._topContainerModuleSpecificCSSClassesWatchHandler = newModule.watch('selectedChildWidget', lang.hitch(this, function() {
					this._removeModuleSpecificCSSClasses();
					this._addModuleSpecificCSSClasses(newModule);
				}));
			}
		},

		_removeModuleSpecificCSSClasses: function() {
			domClass.remove(this._topContainer.domNode, this._topContainerModuleSpecificCSSClasses);
			this._topContainerModuleSpecificCSSClasses = [];
		},

		_addModuleSpecificCSSClasses: function(module) {
			if (!module.selectedChildWidget) {
				// module is still loading
				return;
			}
			Object.keys(module.selectablePagesToLayoutMapping).forEach(lang.hitch(this, function(page) {
				var _pageWidget = lang.getObject(page, false, module);
				if (module.selectedChildWidget === _pageWidget) {
					var pageName = page.toLowerCase().replace(/[^a-z]/g, '');
					var cssClass = lang.replace('umcTopContainer--layout-{moduleID}-{pageName}', {
						moduleID: module.moduleID,
						pageName: pageName
					});
					this._topContainerModuleSpecificCSSClasses.push(cssClass);

					if (lang.exists('moduleFlavor', module)) {
						cssClass = lang.replace('umcTopContainer--layout-{moduleID}-{moduleFlavor}-{pageName}', {
							moduleID: module.moduleID,
							moduleFlavor: module.moduleFlavor.replace(/[^a-zA-Z0-9\-]/g, '-'),
							pageName: pageName
						});
						this._topContainerModuleSpecificCSSClasses.push(cssClass);
					}

					// not sure why we need to check this here since we iterate over module.selectablePagesToLayoutMapping
					if (module.selectablePagesToLayoutMapping[page]) {
						cssClass = lang.replace('umcTopContainer--generic-layout-{layout}', {
							layout: module.selectablePagesToLayoutMapping[page]
						});
						this._topContainerModuleSpecificCSSClasses.push(cssClass);
					}
				}
			}));
			domClass.add(this._topContainer.domNode, this._topContainerModuleSpecificCSSClasses);
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
				return;
			}

			// load module data
			this._loadModules().then(lang.hitch(this, function(args) {
				this._initModuleStore(args.modules, args.categories);
				this._loaded = true;
				this.onLoaded();
			}));
		},

		reloadModules: function() {
			tools.resetModules();
			return this._loadModules(true).then(lang.hitch(this, function(args) {
				if (!_overviewVisible) {
					return;
				}
				this._grid.set('categories', args.categories);
				this._moduleStore.constructor(args.modules, args.categories);

				this._overviewPage.removeChild(this._categoryButtons);
				this.renderCategories();
				// select the previous selected category again (assuming it still exists after reload)
				this._updateQuery(this.category || {id: '_favorites_'});
			}));
		},

		_loadModules: function(reload) {
			var options = reload ? {reload: true} : null;
			return all({
				modules: tools.umcpCommand('get/modules', options),
				categories: tools.umcpCommand('get/categories')
			}).then(lang.hitch(this, function(data) {
				var result = {
					modules: lang.getObject('modules.modules', false, data) || [],
					categories: lang.getObject('categories.categories', false, data) || []
				};
				this._loadJavascriptModules(result.modules);
				return result;
			}));
		},

		_initModuleStore: function(modules, categories) {
			this._moduleStore = this._createModuleStore(modules, categories);
		},

		_createModuleStore: function(modules, categories) {
			return new Observable(new _ModuleStore(modules, categories));
		},

		_loadJavascriptModules: function(modules) {
			// register error handler
			require.on('error', function(err) {
				if (err.message === 'scriptError' && err.info[0].split("/").pop(-1) !== 'piwik.js') {
					dialog.warn(_('Could not load module "%s".', err.info[0]));
					console.log('scriptError:', err);
				}
			});

			var loadedCount = [];

			tools.forEachAsync(modules, lang.hitch(this, function(imod) {
				var is_module = !Boolean(imod.url);
				if (is_module) {
					loadedCount.push(this._tryLoadingModule(imod));
				}
			})).then(lang.hitch(this, function() {
				all(loadedCount).always(lang.hitch(this, 'onModulesLoaded'));
			}));
		},

		_tryLoadingModule: function(module) {
			var deferred = new Deferred();
			deferred.then(null, function(msg) {
				if (msg) {
					console.warn(msg);
				}
			});
			try {
				var path = 'umc/modules/' + module.id;
				require([path], lang.hitch(this, function(baseClass) {
					if (typeof baseClass === "function" && tools.inheritsFrom(baseClass.prototype, 'umc.widgets._ModuleMixin')) {
						deferred.resolve(baseClass);
					} else if (baseClass === null) {
						deferred.cancel(lang.replace('Module could not be loaded: {0}', [path]));
					} else if (typeof baseClass === 'object') {
						require([lang.replace('{0}!{1}', [path, module.flavor || ''])], lang.hitch(this, function(baseClass) {
							if (typeof baseClass === "function" && tools.inheritsFrom(baseClass.prototype, 'umc.widgets._ModuleMixin')) {
								deferred.resolve(baseClass);
							} else {
								deferred.cancel(lang.replace('{0}:{1} is not a umc.widgets._ModuleMixin! (2}', [module.id, module.flavor, baseClass]));
							}
						}));
					} else {
						deferred.cancel(lang.replace('{0} is not a umc.widgets._ModuleMixin! (1}', [module.id, baseClass]));
					}
				}));
			} catch (err) {
				deferred.cancel(err);
			}
			return deferred;
		},

		onLoaded: function() {
			var launchableModules = this._getLaunchableModules();
			if (launchableModules.length < 2) {
				_overviewVisible = false;
			}

			if (launchableModules.length === 1) {
				var state = ioQuery.queryToObject(_initialHash);
				var module = launchableModules[0];
				state.module = lang.replace('{0}:{1}', [module.id, module.flavor || '']);
				_initialHash = decodeURIComponent(ioQuery.objectToQuery(state));
			}
			this.setupGui();

			if (!launchableModules.length) {
				dialog.alert(_('There is no module available for the authenticated user %s.', entities.encode(tools.status('username'))));
			}
		},

		setupGui: function() {
			// make sure that we have not build the GUI before
			if (tools.status('setupGui')) {
				return;
			}

			// set window title
			window.document.title = lang.replace('{0} - {1}', [tools.status('fqdn'), window.document.title]);

			// setup menus
			this._header.setupGui();
			this._setupOverviewPage();
			this._setupStateHashing();

			// set a flag that GUI has been build up
			tools.status('setupGui', true);
			this.onGuiDone();
		},

		// return the index for the given module tab, i.e., the index regarding other
		// open tabs if the same module ID and flavor
		_getModuleTabIndex: function(tab) {
			var idx = 0;
			array.some(this._tabContainer.getChildren(), function(itab) {
				if (itab.id === tab.id) {
					return true;
				}
				if (itab.moduleID === tab.moduleID && itab.moduleFlavor == tab.moduleFlavor) {
					++idx;
				}
			}, this);
			return idx;
		},

		_updateStateHash: function() {
			if (!tools.status('setupStateHashingDone')) {
				return;
			}
			dojoHash(this._getStateHash());
		},

		_getStateHash: function() {
			var moduleTab = lang.getObject('_tabContainer.selectedChildWidget', false, this);
			var state = {};

			if (moduleTab && !moduleTab.isOverview) {
				// module tab
				state.module = lang.replace('{id}:{flavor}:{index}:{state}', {
					id: moduleTab.moduleID,
					flavor: moduleTab.moduleFlavor || '',
					index: this._getModuleTabIndex(moduleTab),
					state: moduleTab.moduleState
				});
			} else if (moduleTab && moduleTab.isOverview && this.category) {
				// overview tab with selected category
				state.category = this.category.id;
			}

			return decodeURIComponent(ioQuery.objectToQuery(state));
		},

		_parseModuleStateHash: function(hash) {
			try {
				var allParts = hash.split(':');
				var mainParts = allParts.splice(0, 3);
				return {
					id: mainParts[0],
					flavor: mainParts[1] || undefined,
					index: mainParts[2] || 0,
					moduleState: allParts.join(':')
				};
			} catch(err) {
				return {};
			}
		},

		_lastStateHash: '',
		_setupStateHashing: function() {
			topic.subscribe('/dojo/hashchange', lang.hitch(this, function(hash) {
				this._handleHash(hash);
			}));
			this._tabContainer.watch('selectedChildWidget', lang.hitch(this, function(name, oldModule, newModule) {
				this._updateStateHash();
			}));

			var hash = _initialHash || this._getStateHash();
			dojoHash(hash, true); // make sure the hash is set in the url
			// call _handleHash once manually since the /dojo/hashchange topic does
			// not fire for dojoHash(hash) if "hash" is already in the URL
			this._handleHash(hash);

			tools.status('setupStateHashingDone', true);
		},

		_handleHash: function(hash) {
			hash = decodeURIComponent(hash);
			if (this._lastStateHash === hash || this._getStateHash() === hash) {
				// nothing to do
				this._lastStateHash = hash;
				return;
			}
			if (!hash) {
				// UMC overview page
				this.switchToOverview();
				return;
			}
			var state = ioQuery.queryToObject(hash);
			if (state.module) {
				var module = this._parseModuleStateHash(state.module);
				var similarModuleTabs = array.filter(this._tabContainer.getChildren(), function(itab) {
					return itab.moduleID === module.id && itab.moduleFlavor == module.flavor;
				});

				if (module.index < similarModuleTabs.length) {
					this.focusTab(similarModuleTabs[module.index]);
					similarModuleTabs[module.index].set('moduleState', module.moduleState);
				} else {
					this.openModule(module.id, module.flavor, {
						moduleState: module.moduleState
					});
				}
			}
			if (state.category) {
				this.switchToOverview();
				var category = this.getCategory(state.category);
				if (category) {
					this._updateQuery(category);
				}
			}

			// save the called parameter
			this._lastStateHash = hash;
		},

		_setupOverviewPage: function() {
			if (!_overviewVisible) {
				return;
			}

			this._grid = new _OverviewPane({
				'class': 'umcOverviewPane',
				categories: this.getCategories(),
				store: this._moduleStore,
				actions: [{
					name: 'open',
					label: _('Open module'),
					isDefaultAction: true,
					callback: lang.hitch(this, function(id, item) {
						if (!item.is_link) {
							this.openModule(item);
						}
					})
				}, {
					name: 'toggle_favorites',
					label: function(item) {
						return isFavorite(item) ? _('Remove from favorites') : _('Add to favorites');
					},
					callback: lang.hitch(this, function(id, item) {
						this._toggleFavoriteModule(item);
						this._updateQuery(this.category);
					})
				}]
			});

			this._overviewPage = new Page({
				noFooter: true,
				id: 'umcOverviewPage',
				title: 'Overview',
				isOverview: true,
				'class': 'umcOverviewContainer container'
			});

			this._searchText = new Text({
				'class': 'dijitDisplayNone umcGalleryCategoryHeader'
			});

			this.renderCategories();
			this._overviewPage.addChild(this._searchText);
			this._overviewPage.addChild(this._grid);
			this._tabContainer.addChild(this._overviewPage, 0);
			this._tabController.hideChild(this._overviewPage);

			aspect.after(this._overviewPage, '_onShow', lang.hitch(this, function() {
				this._grid._resizeItemNames();
			}));
			this._registerGridEvents();

			// show the first visible category
			this._updateQuery(this._lastCategory);
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
				if (has('touch')) {
					styles.insertCssRule(lang.replace('.umcGalleryWrapperItem .umcGalleryCategory-{id}.touched, .umcGalleryWrapperItem.umcGalleryItemActive .umcGalleryCategory-{id}', category), lang.replace('background-color: {0}; ', [color]));
				}
				styles.insertCssRule(lang.replace('.umcGalleryWrapperItem .umcGalleryCategory-{id}:hover, .umcGalleryWrapperItem.umcGalleryItemActive .umcGalleryCategory-{id}', category), lang.replace('background-color: {0}; ', [color]));

				var button = new Button({
					label: category.label,
					'class': lang.replace('umcCategoryButton umcCategory-{id}', category),
					onClick: lang.hitch(this, function() {
						topic.publish('/umc/actions', 'overview', 'category', category.id);
						this._lastCategory = category;
						this._updateQuery(category);

						this._header._search._searchTextBox._updateInlineLabelVisibility();
						this._header._updateTabsVisibility();
					}),
					categoryID: category.id
				});

				// add a node to the button for the colored circle
				var circleNode = put('div.umcCategoryButtonCircleWrapper div.circle + div.dijitIcon.$ <', iconClass);
				domConstruct.place(circleNode, button.titleNode, 'first');
				styles.insertCssRule(lang.replace('.umcCategory-{id} .umcCategoryButtonCircleWrapper .circle', category), lang.replace('background-color: {0};', [color]));

				category._button = button;
				this._categoryButtons.addChild(button);
			}));

			// special treats for an empty favorites category
			var favoritesCategory = this.getCategory('_favorites_');
			var emptyFavorites = this.getModules('_favorites_').length === 0;
			domClass.toggle(favoritesCategory._button.domNode, 'favoritesHidden', emptyFavorites);

			// take the first visible category as fallback for the last selected one
			this._lastCategory = emptyFavorites ? array.filter(this.getCategories(), function(category) { return category.id !== '_favorites_'; })[0] : this.getCategories()[0];

			// spread category buttons over whole width
			styles.insertCssRule('.umc .umcCategoryBar .dijitButton', lang.replace('width: {0}%', [100.0 / this.getCategories().length]));
		},

		_registerGridEvents: function() {
			if (!this._header._search) {
				return;
			}
			this._header._search.on('search', lang.hitch(this, function() {
				this._updateQuery(null);
			}));
		},

		_lastSearchPattern: null,
		_updateQuery: function(category) {
			this.category = category;
			var searchPattern = '';
			var searchQuery = new RegExp('.*');

			if (!this._header._search) {
				return;
			}

			if (!category) {
				searchPattern = lang.trim(this._header._search.get('value'));
				searchQuery = this._header._search.getSearchQuery(searchPattern);
			} else {
				this._lastSearchPattern = null;
				this._header._search.set('value', null);
			}

			if (searchPattern && searchPattern !== this._lastSearchPattern) {
				topic.publish('/umc/actions', 'overview', 'search', searchPattern);
				this._lastSearchPattern = searchPattern;
			}

			if (!category && !searchPattern) {
				// if search pattern is an empty string, resort back to the
				// last selected category
				category = this._lastCategory;
				category._button.set('selected', true);
				this.category = category;
			}

			// update the 'selected' state of all category buttons
			array.forEach(this._categoryButtons.getChildren(), function(ibutton) {
				ibutton.set('selected', category ? ibutton.categoryID === category.id : false);
			});

			this._grid.updateQuery(searchPattern, searchQuery, category);

			// update the search label
			domClass.toggle(this._searchText.domNode, 'dijitDisplayNone', !!category);
			this._searchText.set('content', _('Search query ›%s‹', entities.encode(searchPattern)));

			// update the hash
			this._updateStateHash();
		},

		_updateNumOfTabs: function(offset) {
			// updated number of tabs
			offset = offset || 0;
			tools.status('numOfTabs', Math.max(0, this._tabContainer.getChildren().length - 1 + offset));
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
			if (typeof(module) === 'string') {
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
						return i.moduleID === module.id && i.moduleFlavor == module.flavor;
					});
					if (sameModules.length) {
						tab = sameModules[0];
					}
				}
				if (!tab) {
					// module is not open yet, open it

					// if ther overview is disabled, the first opened module is not closable.
					// Modules opened after that are closable
					var closable = _overviewVisible || this._header._getNumOfTabs() >= 1;

					var params = lang.mixin({
						title: module.name,
						//iconClass: tools.getIconClass(module.icon),
						closable: closable,
						moduleFlavor: module.flavor,
						moduleID: module.id,
						categoryColor: module.category_for_color,
						description: ''
					}, props);

					tab = new BaseClass(params);
					tab.watch('moduleState', lang.hitch(this, '_updateStateHash'));
					this._tabContainer.addChild(tab);
					tab.startup();
					this._updateNumOfTabs();
					this.__insertTabStyles(tab, module);
					topic.publish('/umc/actions', module.id, module.flavor, 'open');
					tools.checkReloadRequired();
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

		_insertedTabStyles: [],
		__insertTabStyles: function(tab, module) {
			var module_flavor_css = module.id;
			if (module.flavor) {
				module_flavor_css = lang.replace('{id}-{flavor}', module);
			}
			module_flavor_css = module_flavor_css.replace(/[^_a-zA-Z0-9\-]/g, '-');

			domClass.add(tab.domNode, lang.replace('color-{0}', [tab.categoryColor]));
			domClass.add(tab.controlButton.domNode, lang.replace('umcModuleTab-{0}', [module_flavor_css]));
			var mobileTab = dojo.byId(`umcMobileTab_${tab.id}`);
			if (mobileTab) {
				domClass.add(mobileTab, lang.replace('color-{0}', [module_flavor_css]));
			}

			var color = this.__getModuleColor(module);
			var dijitTabColor = dojo.colorFromHex(color);
			var contrastLight = umc.tools.contrast(dijitTabColor, '#FFFFFF');
			var contrastDark  = umc.tools.contrast(dijitTabColor, '#1E1E1D');
			domClass.add(tab.controlButton.domNode, contrastDark > contrastLight ? 'contrastDark' : 'contrastLight');

			var styleAlreadyInserted = array.some(this._insertedTabStyles, function(id) {
				return id === module_flavor_css;
			});
			if (styleAlreadyInserted) {
 				return;
 			}
			this._insertedTabStyles.push(module_flavor_css);


			// color the tabs in the tabs dropDownMenu of the umcHeaer
			styles.insertCssRule(
				lang.replace('.umc .umcMobileTab--selected.color-{0}, .umc .umcMobileTab.color-{0}:hover', [module_flavor_css]),
				lang.replace('background-color: {0}', [color])
			);
			var fontColor = contrastDark > contrastLight ? '#1E1E1D' : '#FFFFFF';
			styles.insertCssRule(
				lang.replace('.umc .umcMobileTab--selected.color-{0}, .umc .umcMobileTab.color-{0}:hover', [module_flavor_css]),
				lang.replace('color: {0} !important', [fontColor])
			);

			// color module tabs
			styles.insertCssRule(
				lang.replace('.umc .umcModuleTab-{0}.dijitTabChecked .umcModuleTab__background, .umc .umcModuleTab-{0}.dijitTabHover .umcModuleTab__background, .umc .umcModuleTab-{0}.dijitTabActive .umcModuleTab__background', [module_flavor_css]),
				lang.replace('--tabColor: {0} !important;', [dijitTabColor])
			);
		},

		__getModuleColor: function(module) {
			var category = array.filter(this.getCategories(), lang.hitch(this, function(category) {
				return module.category_for_color === category.id;
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
			destroy = destroy === undefined || destroy === true;
			tab.onClose();
			if (destroy) {
				this._tabContainer.closeChild(tab);
			} else {
				this._tabContainer.removeChild(tab);
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
				// for the favorite category, remove the module from the favorites
				this._moduleStore.removeFavoriteModule(module.id, module.flavor);
				topic.publish('/umc/actions', 'overview', 'favorites', module.id, module.flavor, 'remove');
			}
			else {
				// for any other category, add the module to the favorites
				this._moduleStore.addFavoriteModule(module.id, module.flavor);
				topic.publish('/umc/actions', 'overview', 'favorites', module.id, module.flavor, 'add');
			}
		},

		showPageDialog: function() {
			return this._header.showPageDialog.apply(this, arguments);
		},

		registerOnStartup: function(/*Function*/ callback) {
			topic.publish('/umc/module/startup', callback);
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
					return m.category === category;
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
