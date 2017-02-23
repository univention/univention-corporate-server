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
	"umc/tools",
	"dijit/MenuItem",
	"dijit/PopupMenuItem",
	"dijit/MenuSeparator",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/i18n!",
	"dojo/sniff" // has("ie"), has("ff")
], function(declare, lang, array, on, Deferred, mouse, touch, tap, has, domClass, domConstruct, put, tools, DijitMenuItem, PopupMenuItem, MenuSeparator, _WidgetBase, _TemplatedMixin, ContainerWidget, Text, _) {

	var mobileMenuDeferred = new Deferred();

	var MenuSlide = declare([ContainerWidget], {
		isSubMenu: true,
		label: '',
		'class': 'menuSlide hiddenSlide',
		buildRendering: function() {
			this.inherited(arguments);
			var headerClass = this.isSubMenu ? 'menuSlideHeader subMenu fullWidthTile' : 'menuSlideHeader fullWidthTile';
			this.header = new Text({
				content: this.label,
				'class': headerClass
			});
			this.itemsContainer = new ContainerWidget({
				'class': 'menuSlideItemsContainer'
			});
			this.addChild(this.header);
			this.addChild(this.itemsContainer);
		}
	});

	var SubMenuItem = declare([_WidgetBase, _TemplatedMixin], {
		label: '',
		isSubMenu: true,
		priority: 0,
		parentSlide: null,

		templateString: '' +
			'<div data-dojo-attach-point="contentNode" class="dijitDisplayNone menuItem popupMenuItem fullWidthTile">' +
				'${label}' +
				'<div data-dojo-attach-point="childItemsCounterNode" class="childItemsCounter"></div>' +
				'<div class="popupMenuItemArrow"></div>' +
				'<div class="popupMenuItemArrowActive"></div>' +
			'</div>',

		buildRendering: function() {
			this.inherited(arguments);
			this.menuSlide = new MenuSlide({
				id: this.id + '__slide',
				label: this.label,
				isSubMenu: this.isSubMenu
			});
		},

		getMenuItems: function() {
			return this.menuSlide.itemsContainer.getChildren();
		},

		addMenuItem: function(item) {
			// find the correct position for the entry
			var priorities = array.map(this.getMenuItems(), function(ichild) {
				return ichild.priority || 0;
			});
			var itemPriority = item.priority || 0;
			var pos = 0;
			for (; pos < priorities.length; ++pos) {
				if (itemPriority > priorities[pos]) {
					break;
				}
			}
			this.menuSlide.itemsContainer.addChild(item, pos);
			this._updateCounter();
		},

		_updateCounter: function() {
			var count = array.filter(this.getMenuItems(), function(item) {
				return !domClass.contains(item.domNode, 'separator');
			}).length;
			this.childItemsCounterNode.innerHTML = count;
		},

		open: function(subMenuItem) {
			domClass.remove(this.menuSlide.domNode, 'hiddenSlide');
			domClass.add(this.domNode, 'menuItemActive menuItemActiveTransition');
			tools.defer(lang.hitch(this, function() {
				domClass.replace(this.parentSlide.domNode, 'overlappedSlide', 'topLevelSlide');
				domClass.add(this.menuSlide.domNode, 'visibleSlide topLevelSlide');
			}), 10);
		},

		close: function(subMenuItem) {
			domClass.remove(this.menuSlide.domNode, 'visibleSlide');
			domClass.remove(this.parentSlide.domNode, 'overlappedSlide');
			tools.defer(lang.hitch(this, function() {
				domClass.replace(this.menuSlide.domNode, 'hiddenSlide', 'topLevelSlide');
				domClass.add(this.parentSlide.domNode, 'topLevelSlide');
			}), 510);
			tools.defer(lang.hitch(this, function() {
				domClass.remove(this.domNode, 'menuItemActive');
				tools.defer(lang.hitch(this, function() {
					domClass.remove(this.domNode, 'menuItemActiveTransition');
				}), 400);
			}), 250);
		},

		display: function() {
			domClass.remove(this.domNode, 'dijitDisplayNone');
		}
	});

	var MobileMenu = declare([ContainerWidget], {
		_menuMap: null,
		'class': 'mobileMenu hasPermaHeader',
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
			var userMenuItem = new SubMenuItem({
				id: 'umcMenuMain',
				label: _('Menu'),
				isSubMenu: false
			});
			this._menuMap.umcMenuMain = userMenuItem;
			domClass.replace(userMenuItem.menuSlide.domNode, 'visibleSlide', 'hiddenSlide');
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
				this._mobileButton.closeMobileMenu();
			}));
			dojo.body().appendChild(this._mobileMenuCloseOverlay.domNode);
		},

		_addOrphanedEntries: function(parentMenuId) {
			if (parentMenuId in this._orphanedEntries) {
				array.forEach(this._orphanedEntries[parentMenuId], function(ientry) {
					this.addMenuEntry(ientry);
				}, this);
				delete this._orphanedEntries[parentMenuId];
			}
		},

		addSubMenu: function(/*Object*/ item) {
			// adds a menu entry that when clicked opens a submenu.
			// Menu entries or other sub-menus can be added to this sub-menu.
			//
			// takes an object as paramter with the following properties:
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
					parentSlide: lang.getObject('menuSlide', false, parentMenuItem),
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
			_addClickListeners(subMenuItem);
			parentMenuItem.addMenuItem(subMenuItem);
			this._addOrphanedEntries(item.id);
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
				this._handleDeprecatedMenuInstances(item);
				return;
			}

			var _createMenuEntry = function() {
				if (!item.onClick && !item.label) {
					return new Text({
						id: item.id,
						'class': 'menuItem separator fullWidthTile'
					});
				}
				var menuEntry = new Text({
					priority: item.priority || 0,
					content: item.label,
					id: item.id,
					'class': 'menuItem fullWidthTile'

				});
				menuEntry.domNode.onclick = function() {
					item.onClick();
				};
				return menuEntry;
			};

			// start: creating menu entry
			var parentMenuId = item.parentMenuId || 'umcMenuMain';
			var parentMenuItem = this._menuMap[parentMenuId];

			if (!parentMenuItem) {
				// parent menu does not exist... save entry to be added later
				var parentEntries = this._orphanedEntries[item.parentMenuId] || [];
				parentEntries.push(item);
				this._orphanedEntries[item.parentMenuId] = parentEntries;
				return;
			}

			parentMenuItem.display();
			var menuEntry = _createMenuEntry();
			parentMenuItem.addMenuItem(menuEntry);
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
				this.addSubMenu(newSubmenu);
			} else if (item.isInstanceOf(DijitMenuItem)) {
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
