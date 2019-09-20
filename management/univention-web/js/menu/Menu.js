/*
 * Copyright 2017-2019 Univention GmbH
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
/*global define,require,dojo*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/Deferred",
	"dojo/topic",
	"dojox/gesture/tap",
	"dojo/dom-class",
	"dijit/MenuItem",
	"dijit/PopupMenuItem",
	"dijit/MenuSeparator",
	"umc/tools",
	"umc/menu/MenuItem",
	"umc/menu/SubMenuItem",
	"umc/menu/_Button",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/i18n!"
], function(declare, lang, array, on, Deferred, topic, tap, domClass, DijitMenuItem, PopupMenuItem, MenuSeparator, tools, MenuItem, SubMenuItem, _Button, ContainerWidget, Text, _) {

	// require umc/menu here in order to avoid circular dependencies
	var menuDeferred = new Deferred();
	require(["umc/menu"], function(_menu) {
		menuDeferred.resolve(_menu);
	});

	var mobileMenuDeferred = new Deferred();

	require(['login'], function(login) {
		// react to login/logout events
		login.onLogin(function() {
			// user has logged in -> set username and host in menu header
			mobileMenuDeferred.then(function(menu) {
				menu.informationHeader.username.set('content', tools.status('username'));
				menu.informationHeader.host.set('content', lang.replace('@{0}', [tools.status('hostname')]));
			});
		});

		login.onLogout(function() {
			// user has logged out -> unset username and host in menu header
			mobileMenuDeferred.then(function(menu) {
				menu.informationHeader.username.set('content', '');
				menu.informationHeader.host.set('content', '');
			});
		});
	});

	var MobileMenu = declare('umc.menu.Menu', [ContainerWidget], {
		_menuMap: null,
		'class': 'mobileMenu',
		menuSlides: null,
		permaHeader: null,
		popupHistory: null,

		// save entries which have no parent yet
		_orphanedEntries: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.popupHistory = [];
			this._orphanedEntries = {};
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._menuMap = {};

			this.addButton();
			this.addInformationHeader();
			this.addMenuSlides();
			this.addUserMenu();
			this.addPermaHeader();
			this.addCloseOverlay();
			dojo.body().appendChild(this.domNode);
		},

		postCreate: function() {
			this.inherited(arguments);
			mobileMenuDeferred.resolve(this);
		},

		addInformationHeader: function() {
			var username = new Text({
				'class': 'menuInformationHeaderUsername'
			});
			var host = new Text({
				'class': 'menuInformationHeaderHostname'
			});
			this.informationHeader = new ContainerWidget({
				'class': 'menuInformationHeader',
				username: username,
				host: host
			});
			this.informationHeader.addChild(username);
			this.informationHeader.addChild(host);
			this.addChild(this.informationHeader);
		},

		addMenuSlides: function() {
			var menuSlides = new ContainerWidget({
				'class': 'menuSlides popupSlideNormalTransition overlappedSlidePushTransition'
			});
			this.menuSlides = menuSlides;
			this.addChild(menuSlides);
		},

		addUserMenu: function() {
			var userMenuItem = new SubMenuItem({
				id: 'umcMenuMain',
				label: _('Menu'),
				isSubMenu: false
			});
			this._menuMap.umcMenuMain = userMenuItem;
			domClass.replace(userMenuItem.menuSlide.domNode, 'visibleSlide', 'hiddenSlide');
			domClass.add(userMenuItem.menuSlide.domNode, 'mainSlide');
			this.menuSlides.addChild(userMenuItem.menuSlide);
		},

		addPermaHeader: function() {
			// create permaHeader
			var permaHeader = new Text({
				content: 'Menu',
				'class': 'menuSlideHeader permaHeader fullWidthTile'
			});
			this.permaHeader = permaHeader;
			this.addChild(permaHeader);

			// add listeners
			this.permaHeader.on(tap, lang.hitch(this, function() {
				var lastClickedSubMenuItem = this.popupHistory.pop();

				this._updateMobileMenuPermaHeaderForClosing(lastClickedSubMenuItem);
				lastClickedSubMenuItem.close();
			}));
		},

		addButton: function() {
			this.addChild(new _Button());
		},

		_updateMobileMenuPermaHeaderForClosing: function(subMenuItem) {
			if (!subMenuItem) {
				return;
			}
			this.permaHeader.set('content', subMenuItem.parentSlide.header.content);
			var isSubMenu = domClass.contains(subMenuItem.parentSlide.header.domNode, 'subMenu');
			domClass.toggle(this.permaHeader.domNode, 'subMenu', isSubMenu);
		},

		addCloseOverlay: function() {
			this._mobileMenuCloseOverlay = new ContainerWidget({
				'class': 'mobileMenuCloseOverlay'
			});
			this._mobileMenuCloseOverlay.on(tap, lang.hitch(this, function() {
				menuDeferred.then(function(menu) {
					menu.close();
				});
			}));
			dojo.body().appendChild(this._mobileMenuCloseOverlay.domNode);
		},

		closeOpenedSubMenus: function() {
			// resets the menu to the first slide
			var firstClickedSubMenuItem = this.popupHistory[0];
			if (!firstClickedSubMenuItem) {
				return;
			}

			do {
				this.popupHistory.pop().close();
			} while (this.popupHistory.length);
			this._updateMobileMenuPermaHeaderForClosing(firstClickedSubMenuItem);
		},

		_registerOrphanedEntry: function(menuEntry, parentMenuId) {
			// parent menu does not exist... save entry to be added later
			var parentEntries = this._orphanedEntries[parentMenuId] || [];
			parentEntries.push(menuEntry);
			this._orphanedEntries[parentMenuId] = parentEntries;
		},

		_mergeOrphanedEntries: function(parentMenuId) {
			if (parentMenuId in this._orphanedEntries) {
				var parentMenuItem = this._menuMap[parentMenuId];
				array.forEach(this._orphanedEntries[parentMenuId], function(ientry) {
					if (ientry instanceof SubMenuItem) {
						ientry.set('parentSlide', lang.getObject('menuSlide', false, parentMenuItem));
					}
					parentMenuItem.addMenuItem(ientry);
				});
				delete this._orphanedEntries[parentMenuId];
			}
		},

		addSubMenu: function(/*Object*/ item) {
			// adds a menu entry that when clicked opens a submenu.
			// Menu entries or other sub-menus can be added to this sub-menu.
			//
			// takes an object as parameter with the following properties:
			//	Required:
			//		label: String
			//  Optional:
			//		priority: Number
			//			The priority affects at which position the MenuItem will be placed in the parent menu.
			//			The highest number is the first Menu entry, the lowest number the last.
			//			Defaults to 0.
			//		parentMenuId: String
			//			The id of the parentMenu as String. The Menu entry will be the child of that parent if it exists.
			//			Defaults to 'umcMenuMain'.
			//		id: String

			// function definitions (jump to 'start')
			var _createSubMenuItem = lang.hitch(this, function() {
				var subMenuItem = new SubMenuItem({
					isSubMenu: true,
					label: item.label,
					id: item.id,
					priority: item.priority || 0,
					content: item.label,
					parentSlide: lang.getObject('menuSlide', false, parentMenuItem)
				});
				this._menuMap[item.id] = subMenuItem;
				this.menuSlides.addChild(subMenuItem.menuSlide);
				return subMenuItem;
			});

			var _addClickListeners = lang.hitch(this, function(subMenuItem) {
				// open the slide of the subMenuItem
				subMenuItem.on(tap , lang.hitch(this, function() {
					subMenuItem.open();
					this._updateMobileMenuPermaHeaderForOpening(subMenuItem);
				}));

				// close the slide of the subMenuItem
				subMenuItem.menuSlide.header.on(tap , lang.hitch(this, function() {
					var lastClickedSubMenuItem = this.popupHistory.pop();

					lastClickedSubMenuItem.close();
					this._updateMobileMenuPermaHeaderForClosing(subMenuItem);
				}));
			});

			// start: creating sub menu
			var parentMenuId = item.parentMenuId || 'umcMenuMain';
			var parentMenuItem = this._menuMap[parentMenuId];
			var subMenuItem = _createSubMenuItem();
			this._mergeOrphanedEntries(item.id);
			_addClickListeners(subMenuItem);

			if (!parentMenuItem) {
				this._registerOrphanedEntry(subMenuItem, parentMenuId);
				return subMenuItem;
			}

			parentMenuItem.addMenuItem(subMenuItem);
			return subMenuItem;
		},

		_updateMobileMenuPermaHeaderForOpening: function(subMenuItem) {
			this.permaHeader.set('content', subMenuItem.menuSlide.header.content);
			this.popupHistory.push(subMenuItem);
			domClass.toggle(this.permaHeader.domNode, 'subMenu', domClass.contains(subMenuItem.menuSlide.header.domNode, 'subMenu'));
		},

		addMenuEntry: function(/*Object*/ item) {
			// takes an object as parameter with the following properties:
			//	Required:
			//		label: String
			//		onClick: Function
			//	Optional:
			//		priority: Number
			//			The priority affects at which position the MenuItem will be placed in the parent menu.
			//			The highest number is the first Menu entry, the lowest number the last.
			//			Defaults to 0.
			//		parentMenuId: String
			//			The id of the parentMenu as String. The Menu entry will be the
			//			child of that parent if it exists.
			//			Defaults to 'umcMenuMain'
			//		id: String
			//
			//  To insert a Menu separator leave out the required parameters. Any or none optional parameters can still be passed.

			// handle old uses of addMenuEntry
			if (item.isInstanceOf &&
					(item.isInstanceOf(DijitMenuItem) ||
					item.isInstanceOf(PopupMenuItem) ||
					item.isInstanceOf(MenuSeparator)) ) {
				return this._handleDeprecatedMenuInstances(item);
			}

			var _createMenuEntry = function() {
				return new MenuItem({
					id: item.id || null,
					priority: item.priority || 0,
					label: item.label || '',
					disabled: item.disabled || false,
					onClick: item.onClick
				});
			};

			// start: creating menu entry
			var parentMenuId = item.parentMenuId || 'umcMenuMain';
			var parentMenuItem = this._menuMap[parentMenuId];
			var menuEntry = _createMenuEntry();

			// add listeners if entry is not a separator
			if (typeof menuEntry.onClick === 'function') {
				menuEntry.on(tap, function() {
					menuEntry.onClick();
					menuDeferred.then(function(menu) {
						menu.close();
					});
				});
			}

			if (!parentMenuItem) {
				this._registerOrphanedEntry(menuEntry, parentMenuId);
				return menuEntry;
			}

			parentMenuItem.addMenuItem(menuEntry);
			return menuEntry;
		},

		addMenuSeparator: function(/*Object*/ item) {
			// takes an object as parameter with the following properties:
			//	Optional:
			//		priority: Number
			//			The priority affects at which position the MenuItem will be placed in the parent menu.
			//			The highest number is the first Menu entry, the lowest number the last.
			//			Defaults to 0.
			//		parentMenuId: String
			//			The id of the parentMenu as String. The Menu entry will be the
			//			child of that parent if it exists.
			//			Defaults to 'umcMenuMain'
			//		id: String

			var _item = {
				priority: item ? item.priority : undefined,
				parentMenuId: item ? item.parentMenuId : undefined,
				id: item ? item.id : undefined
			};
			return this.addMenuEntry(_item);
		},

		_handleDeprecatedMenuInstances: function(item) {
			if (item.isInstanceOf(PopupMenuItem)) {
				// create submneu
				var newSubmenu = {
					parentMenuId: item.$parentMenu$,
					priority: item.$priority$,
					label: item.label,
					id: item.id
				};

				// add menu entries to submenu
				if (item.popup && item.popup.getChildren().length > 0) {
					var menuEntries = item.popup.getChildren();
					array.forEach(menuEntries, function(menuEntry) {
						var newEntry = {
							parentMenuId: item.id,
							priority: menuEntry.$priority$ || 0,
							label: menuEntry.label,
							onClick: menuEntry.onClick
						};
						this.addMenuEntry(newEntry);
					}, this);
				}
				// destroy deprecated menu instance
				item.destroyRecursive();
				return this.addSubMenu(newSubmenu);
			}
			if (item.isInstanceOf(DijitMenuItem)) {
				var newEntry = {
					parentMenuId: item.$parentMenu$ || "",
					priority: item.$priority$ || 0,
					id: item.id,
					label: item.label,
					onClick: item.onClick
				};
				item.destroyRecursive();
				return this.addMenuEntry(newEntry);
			}
			if (item.isInstanceOf(MenuSeparator)) {
				var newSeperator = {
					parentMenuId: item.$parentMenu$,
					priority: item.$priority$ || 0,
					id: item.id
				};
				item.destroyRecursive();
				return this.addMenuEntry(newSeperator);
			}
		}
	});

	MobileMenu.mobileMenuDeferred = mobileMenuDeferred;
	return MobileMenu;
});
