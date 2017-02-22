/*
 * Copyright 2017 Univention GmbH
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
/*global define,dojo*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/Deferred",
	"dojo/mouse",
	"dojo/touch",
	"dojox/gesture/tap",
	"dojo/has",
	"dojo/dom-class",
	"dojo/dom-construct",
	"put-selector/put",
	"dijit/registry",
	"umc/tools",
	"dijit/MenuItem",
	"dijit/PopupMenuItem",
	"dijit/MenuSeparator",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/i18n!",
	"dojo/sniff" // has("ie"), has("ff")
], function(declare, lang, array, on, Deferred, mouse, touch, tap, has, domClass, domConstruct, put, registry, tools, MenuItem, PopupMenuItem, MenuSeparator, ContainerWidget, Text, _) {

	var mobileMenuDeferred = new Deferred();

	var MobileMenu = declare([ContainerWidget], {
		_menuMap: null,
		'class': 'mobileMenu hasPermaHeader',
		menuSlides: null,
		permaHeader: null,
		popupHistory: [],

		buildRendering: function() {
			this.inherited(arguments);
			this._menuMap = {};

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

		addMenuSlides: function() {
			var menuSlides = new ContainerWidget({
				'class': 'menuSlides popupSlideNormalTransition'
			});
			this.menuSlides = menuSlides;
			this.addChild(menuSlides);
		},

		addUserMenu: function() {
			var userMenu = this._buildMenuSlide('umcMenuMain', _('Menu'));
			domClass.replace(userMenu.domNode, 'visibleSlide', 'hiddenSlide');
			this.menuSlides.addChild(userMenu);
			this._menuMap[userMenu.id] = userMenu.menuSlideItemsContainer;
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
				var lastClickedPopupMenuItem = this.popupHistory.pop();

				this._updateMobileMenuPermaHeaderForClosing(lastClickedPopupMenuItem);
				this._closeMobileMenuPopupFor(lastClickedPopupMenuItem);
			}));
		},

		_updateMobileMenuPermaHeaderForClosing: function(popupMenuItem) {
			if (!popupMenuItem) {
				return;
			}
			this.permaHeader.set('content', popupMenuItem.parentSlide.menuSlideHeader.content);
			var isSubMenu = domClass.contains(popupMenuItem.parentSlide.menuSlideHeader.domNode, 'subMenu');
			domClass.toggle(this.permaHeader.domNode, 'subMenu', isSubMenu);
		},

		_closeMobileMenuPopupFor: function(popupMenuItem) {
			if (!popupMenuItem) {
				return;
			}
			domClass.remove(popupMenuItem.popup.domNode, 'visibleSlide');
			domClass.remove(popupMenuItem.parentSlide.domNode, 'overlappedSlide');
			tools.defer(function() {
				domClass.replace(popupMenuItem.popup.domNode, 'hiddenSlide', 'topLevelSlide');
				domClass.add(popupMenuItem.parentSlide.domNode, 'topLevelSlide');
			}, 510);
			tools.defer(function() {
				domClass.remove(popupMenuItem.domNode, 'menuItemActive');
				tools.defer(function() {
					domClass.remove(popupMenuItem.domNode, 'menuItemActiveTransition');
				}, 400);
			}, 250);
		},

		addCloseOverlay: function() {
			this._mobileMenuCloseOverlay = new ContainerWidget({
				'class': 'mobileMenuCloseOverlay'
			});
			this._mobileMenuCloseOverlay.on(tap, lang.hitch(this, function() {
				this._mobileButton.closeMobileMenu();
			}));
			dojo.body().appendChild(this._mobileMenuCloseOverlay.domNode);
		},

		_buildMenuSlide: function(id, label, isSubMenu) {
			var headerClass = isSubMenu ? 'menuSlideHeader subMenu fullWidthTile' : 'menuSlideHeader fullWidthTile';
			var menuSlideHeader = new Text({
				content: label,
				'class': headerClass
			});
			var menuSlideItemsContainer = new ContainerWidget({
				'class': 'menuSlideItemsContainer'
			});

			var menuSlide = new ContainerWidget({
				id: id,
				'class': 'menuSlide hiddenSlide',
				menuSlideHeader: menuSlideHeader,
				menuSlideItemsContainer: menuSlideItemsContainer,
				popupMenuItem: null
			});
			menuSlide.addChild(menuSlideHeader);
			menuSlide.addChild(menuSlideItemsContainer);

			return menuSlide;
		},

		addSubMenu: function(/*Object*/ item) {
			// adds a menu entry that when clicked opens a submenu.
			// Menu entries or other sub-menus can be added to this sub-menu.
			//
			// takes an object as paramter with the following properties:
			//	Required:
			//		label: String
			//		popup: Object[]
			//			Array of objects. Each object defines a menu entry that will be a child of
			//			this sub-menu.
			//			The objects needs to be in the format described at the 'addMenuEntry' method.
			//			Can be empty.
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
			var _createPopupMenuItem = lang.hitch(this, function() {
				var _menuSlide = this._buildMenuSlide(item.id, item.label, true);
				var _parentSlide = registry.byId(item.parentMenuId || defaultParentMenu);
				var childItemsCounterNode = domConstruct.create('div', {
					'class': 'childItemsCounter'
				});
				popupMenuItem = new Text({
					priority: item.priority || 0,
					content: _(item.label),
					popup: _menuSlide,
					parentSlide: _parentSlide,
					childItemsCounter: 0,
					childItemsCounterNode: childItemsCounterNode,
					'class': 'dijitHidden menuItem popupMenuItem fullWidthTile'
				});
				// store a reference to the popupMenuItem in its popup
				popupMenuItem.popup.popupMenuItem = popupMenuItem;

				put(popupMenuItem.domNode, childItemsCounterNode, '+ div.popupMenuItemArrow + div.popupMenuItemArrowActive');

				this.menuSlides.addChild(popupMenuItem.popup);
				this._menuMap[popupMenuItem.popup.id] = popupMenuItem.popup.menuSlideItemsContainer;

				_addClickListeners();
			});

			var _addClickListeners = lang.hitch(this, function() {
				// open the popup of the popupMenuItem
				popupMenuItem.on(tap , lang.hitch(this, function() {
					this._openMobileMenuPopupFor(popupMenuItem);
					this._updateMobileMenuPermaHeaderForOpening(popupMenuItem);
				}));

				// close the popup of the popupMenuItem
				popupMenuItem.popup.menuSlideHeader.on(tap , lang.hitch(this, function() {
					var lastClickedPopupMenuItem = this.popupHistory.pop();

					this._closeMobileMenuPopupFor(lastClickedPopupMenuItem);
					this._updateMobileMenuPermaHeaderForClosing(popupMenuItem);
				}));
			});

			var _addChildEntries = lang.hitch(this, function() {
				// add MenuEntries to the subMenu
				if (item.popup && item.popup.length > 0) {
					array.forEach(item.popup, lang.hitch(this, function(menuEntry) {
						menuEntry.parentMenuId = popupMenuItem.popup.id;
						if (menuEntry.popup) {
							this.addSubMenu(menuEntry);
						} else {
							this.addMenuEntry(menuEntry);
						}
					}));
				}
			});

			var _inserPopupMenuItem = lang.hitch(this, function() {
				// add the submenu at the correct position
				var menu = this._menuMap[item.parentMenuId || defaultParentMenu];

				// find the correct position for the entry
				var priorities = array.map(menu.getChildren(), function(ichild) {
					return ichild.priority || 0;
				});
				var itemPriority = item.priority || 0;
				var pos = 0;
				for (; pos < priorities.length; ++pos) {
					if (itemPriority > priorities[pos]) {
						break;
					}
				}
				menu.addChild(popupMenuItem, pos);
			});

			var _incrementPopupMenuItemCounter = function() {
				var parentMenu = registry.byId(item.parentMenuId || defaultParentMenu);
				if (parentMenu && parentMenu.popupMenuItem) {
					parentMenu.popupMenuItem.childItemsCounter++;
					parentMenu.popupMenuItem.childItemsCounterNode.innerHTML = parentMenu.popupMenuItem.childItemsCounter;
				}
			};

			// start: creating sub menu
			var defaultParentMenu = 'umcMenuMain';
			var popupMenuItem;

			_createPopupMenuItem();
			_addChildEntries();
			_inserPopupMenuItem();
			_incrementPopupMenuItemCounter();
		},

		_openMobileMenuPopupFor: function(popupMenuItem) {
			domClass.remove(popupMenuItem.popup.domNode, 'hiddenSlide');
			domClass.add(popupMenuItem.domNode, 'menuItemActive menuItemActiveTransition');
			tools.defer(function() {
				domClass.replace(popupMenuItem.parentSlide.domNode, 'overlappedSlide', 'topLevelSlide');
				domClass.add(popupMenuItem.popup.domNode, 'visibleSlide topLevelSlide');
			}, 10);
		},

		_updateMobileMenuPermaHeaderForOpening: function(popupMenuItem) {
			this.permaHeader.set('content', popupMenuItem.popup.menuSlideHeader.content);
			this.popupHistory.push(popupMenuItem);
			domClass.toggle(this.permaHeader.domNode, 'subMenu', domClass.contains(popupMenuItem.popup.menuSlideHeader.domNode, 'subMenu'));
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

			if (!tools.status('overview')) {
				return;
			}

			// handle old uses of addMenuEntry
			if (item.isInstanceOf &&
					(item.isInstanceOf(MenuItem) ||
					item.isInstanceOf(PopupMenuItem) ||
					item.isInstanceOf(MenuSeparator)) ) {
				this._handleDeprecatedMenuInstances(item);
				return;
			}

			// function definitions (jump to 'start')
			var _unhideParent = function() {
				// unhide the parent menu in case it is hidden
				if (parentMenu && parentMenu.popupMenuItem) {
					domClass.remove(parentMenu.popupMenuItem.domNode, 'dijitHidden');
				}
			};

			var _createMenuEntry = function() {
				if (!item.onClick && !item.label) {
					menuEntry = new Text({
						id: item.id,
						'class': 'menuItem separator fullWidthTile'
					});
				} else {
					menuEntry = new Text({
						priority: item.priority || 0,
						content: _(item.label),
						id: item.id,
						'class': 'menuItem fullWidthTile'

					});
					menuEntry.domNode.onclick = function() {
						item.onClick();
					};
				}
			};

			var _insertMenuEntry = lang.hitch(this, function() {
				// add the menuEntry to the correct menu
				var menu = this._menuMap[item.parentMenuId || defaultParentMenu];

				// find the correct position for the entry
				var priorities = array.map(menu.getChildren(), function(ichild) {
					return ichild.priority || 0;
				});
				var itemPriority = item.priority || 0;
				var pos = 0;
				for (; pos < priorities.length; ++pos) {
					if (itemPriority > priorities[pos]) {
						break;
					}
				}

				menu.addChild(menuEntry, pos);
			});

			var _incrementPopupMenuItemCounter = function() {
				// increase counter of the popupMenuItem
				if (!domClass.contains(menuEntry.domNode, 'separator')) {
					if (parentMenu && parentMenu.popupMenuItem) {
						parentMenu.popupMenuItem.childItemsCounter++;
						parentMenu.popupMenuItem.childItemsCounterNode.innerHTML = parentMenu.popupMenuItem.childItemsCounter;
					}
				}
			};

			// start: creating menu entry
			var defaultParentMenu = 'umcMenuMain';
			var parentMenu = registry.byId(item.parentMenuId);
			var menuEntry;

			_unhideParent();
			_createMenuEntry();
			_insertMenuEntry();
			_incrementPopupMenuItemCounter();
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
			this.addMenuEntry(_item);
		},

		_handleDeprecatedMenuInstances: function(item) {
			if (item.isInstanceOf(PopupMenuItem)) {
				// create submneu
				var newSubmenu = {
					parentMenuId: item.$parentMenu$,
					priority: item.$priority$,
					label: item.label,
					popup: [],
					id: item.id
				};
				// add menu entries to submenu
				if (item.popup && item.popup.getChildren().length > 0) {
					var menuEntries = item.popup.getChildren();
					array.forEach(menuEntries, function(menuEntry) {
						var newEntry = {
							priority: menuEntry.$priority$ || 0,
							label: menuEntry.label,
							onClick: menuEntry.onClick
						};
						newSubmenu.popup.push(newEntry);
					});
				}
				// destroy deprecated menu instance
				item.destroyRecursive();
				this.addSubMenu(newSubmenu);
			} else if (item.isInstanceOf(MenuItem)) {
				var newEntry = {
					parentMenuId: item.$parentMenu$ || "",
					priority: item.$priority$ || 0,
					id: item.id,
					label: item.label,
					onClick: item.onClick
				};
				item.destroyRecursive();
				this.addMenuEntry(newEntry);
			} else if (item.isInstanceOf(MenuSeparator)) {
				var newSeperator = {
					parentMenuId: item.$parentMenu$,
					priority: item.$priority$ || 0,
					id: item.id
				};
				item.destroyRecursive();
				this.addMenuEntry(newSeperator);
			}
		}
	});

	var menuButtonDeferred = new Deferred();

	var MenuButton = declare('umc.MenuButton', [ContainerWidget], {
		'class': 'umcMobileMenuToggleButton',

		mobileToggleMouseLeave: null,

		buildRendering: function() {
			this.inherited(arguments);
			this._mobileMenu = new MobileMenu({_mobileButton: this});

			// create hamburger stripes
			put(this.domNode, 'div + div + div + div.umcMobileMenuToggleButtonTouchStyle');

			// add listeners
			if (has('touch')) {
				this.on(touch.press, function() {
					domClass.add(this, 'umcMobileMenuToggleButtonTouched');
				});
				this.on([touch.leave, touch.release], function() {
					tools.defer(lang.hitch(this, function() {
						domClass.remove(this, 'umcMobileMenuToggleButtonTouched');
					}), 300);
				});
			} else {
				this.on(mouse.enter, function() {
					domClass.add(this, 'umcMobileMenuToggleButtonHover');
				});
				this.mobileToggleMouseLeave = on.pausable(this.domNode, mouse.leave, function() {
					domClass.remove(this, 'umcMobileMenuToggleButtonHover');
				});
			}
			this.on(tap, lang.hitch(this, 'toggleButtonClicked'));
		},

		postCreate: function() {
			this.inherited(arguments);
			menuButtonDeferred.resolve(this);
		},

		toggleButtonClicked: function() {
			if (this.mobileToggleMouseLeave) {
				this.mobileToggleMouseLeave.pause();
			}
			tools.defer(lang.hitch(this, function() {
				domClass.remove(this.domNode, 'umcMobileMenuToggleButtonHover');
			}, 510)).then(lang.hitch(this, function() {
				if (this.mobileToggleMouseLeave) {
					this.mobileToggleMouseLeave.resume();
				}
			}));
			if (domClass.contains(dojo.body(), 'mobileMenuActive')) {
				this.closeMobileMenu();
			} else {
				this.openMobileMenu();
			}
		},

		openMobileMenu: function() {
			domClass.toggle(dojo.body(), 'mobileMenuActive');
			tools.defer(function() {
				domClass.toggle(dojo.body(), 'mobileMenuToggleButtonActive');
			}, 510);
		},

		closeMobileMenu: function() {
			if (!domClass.contains(dojo.body(), 'mobileMenuActive')) {
				return;
			}
			domClass.remove(dojo.body(), 'mobileMenuActive');
			tools.defer(function() {
				domClass.toggle(dojo.body(), 'mobileMenuToggleButtonActive');
			}, 510);
		}
	});

	MenuButton.menuButtonDeferred = menuButtonDeferred;
	MenuButton.mobileMenuDeferred = mobileMenuDeferred;

	return MenuButton;
});
