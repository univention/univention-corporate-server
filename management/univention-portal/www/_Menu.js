/*
 * Copyright 2020 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/PopupMenuItem",
	"umc/tools",
	"umc/i18n!"
], function(declare, lang, domClass, Menu, MenuItem, PopupMenuItem, tools, _) {
	return declare('portal._Menu', [Menu], {
		$wrapper: null,

		// used to have a unique selector for the popup created by dijit/popup; which is baseClass + 'Popup'
		baseClass: 'portalMenu', // this does not seem to break styling but dijit/_CssStateMixin is still behaving weird

		_queuedMenuItems: null,
		_queuedPopupMenuItems: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this._queuedMenuItems = [];
			this._queuedPopupMenuItems = [];
		},

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'materialMenu');

			// This is a hacky workaround.
			//
			// dijit/popup - which opens the dropdown of an Widget that mixes dijit/_HasDropDown in -
			// checks for special functions and calls them if they exist on the dropdown.
			// dijit/_MenuBase provides these functions which handle that the menu and submenus are
			// closed correctly when canceling or clicking on an dijit/MenuItem.
			//
			// For the portal/UserMenu we want to show the username of the logged in user above the menu
			// but if we use e.g. a ContainerWidget that holds the username text and the menu as dropdown
			// then the dropdown wont close correctly on cancel and clicking since the ContainerWidget
			// does not have all the functions dijit/_MenuBase provides.
			//
			// So we just change this.domNode to our desired container (which holds this dijit/Menu instance)
			// Luckily the places where this.domNode is used in dijit/Menu (and the parent classes) does not care
			// if it is actually the dijit/Menu domNode.
			if (this.$wrapper) {
				domClass.add(this.$wrapper.domNode, 'materialPopup');
				this.$wrapper.addChild(this);
				this.domNode = this.$wrapper.domNode;
			}
		},

		// adds an MenuItem or PopupMenuItem depending on the attributes of conf
		//
		// conf is an object which is used as argument to MenuItem/PopupMenuItem
		// e.g. new MenuItem(conf) / new PopupMenuItem(conf)
		// You can't define your own popup for an PopupMenuItem. conf.popup will
		// be overwritten by addPopupMenuItem.
		//
		// conf can/must contain some special attributes. These are
		// $id: string - can be used to hide/show the added menu item
		// $parentMenuId: string - add this menu item to the menu with $id === $parentMenuId. If $parentMenuId is not provided then the item will be added to the top level menu
		// $priority: int - used for sorting the menu items. The higher the value, the lower in the menu. Defaults to 0
		addItem: function(conf) {
			if (conf.onClick) {
				this.addMenuItem(conf);
			} else {
				this.addPopupMenuItem(conf);
			}
		},

		addPopupMenuItem: function(conf) {
			if (!conf.$id) {
				console.warn('portal/_Menu: addPopupMenuItem(conf): conf.$id is missing');
				return;
			}

			var parentMenu = !!conf.$parentMenuId ? this._findParentMenu(conf.$parentMenuId) : this;
			if (!parentMenu) {
				if (!conf.$queued) {
					conf.$queued = true;
					this._queuedPopupMenuItems.push(conf);
				}
				return false;
			}
			delete conf.$queued;

			conf = lang.mixin(conf, {
				popup: new Menu({
					'class': 'materialMenu materialPopup'
				})
			});
			parentMenu.addChild(new PopupMenuItem(conf));
			this._sortMenuItems(parentMenu);
			this._dequeueMenuItems();
			return true;
		},

		addMenuItem: function(conf) {
			var parentMenu = !!conf.$parentMenuId ? this._findParentMenu(conf.$parentMenuId) : this;
			if (!parentMenu) {
				if (!conf.$queued) {
					conf.$queued = true;
					this._queuedMenuItems.push(conf);
				}
				return false;
			}
			delete conf.$queued;

			parentMenu.addChild(new MenuItem(conf));
			this._sortMenuItems(parentMenu);
			return true;
		},

		_findParentMenu: function(parentMenuId) {
			var findParentMenu = function(menu) {
				var parentMenu = null;
				var menuItems = menu.getChildren();
				for (var x = 0; x < menuItems.length; x++) {
					var menuItem = menuItems[x];
					if (menuItem.popup) {
						parentMenu = menuItem.$id === parentMenuId ? menuItem.popup : findParentMenu(menuItem.popup);
						if (parentMenu) {
							break;
						}
					}
				}
				return parentMenu;
			};
			return findParentMenu(this);
		},

		_sortMenuItems: function(menu) {
			var menuItems = menu.getChildren();
			menuItems.forEach(function(_menuItem) {
				menu.removeChild(_menuItem);
			});
			menuItems.sort(function(a, b) {
				var prioA = a.$priority || 0;
				var prioB = b.$priority || 0;
				return prioA - prioB;
			});
			menuItems.forEach(function(_menuItem) {
				menu.addChild(_menuItem);
			});
		},

		_dequeueMenuItems: function() {
			var dequeuePopupMenuItems = lang.hitch(this, function() {
				var lastLength = this._queuedPopupMenuItems.length;
				for (var x = 0; x < this._queuedPopupMenuItems.length; /* deliberately ommited */) {
					var wasAdded = this.addPopupMenuItem(this._queuedPopupMenuItems[x]);
					if (wasAdded) {
						this._queuedPopupMenuItems.splice(x, 1);
					} else {
						x++;
					}
				}
				// if we dequeued a PopupMenuItem than we can maybe dequeue another one
				if (lastLength !== this._queuedPopupMenuItems.length) {
					dequeuePopupMenuItems();
				}
			});
			dequeuePopupMenuItems();

			for (var x = 0; x < this._queuedMenuItems.length; /* deliberately ommited */) {
				var wasAdded = this.addMenuItem(this._queuedMenuItems[x]);
				if (wasAdded) {
					this._queuedMenuItems.splice(x, 1);
				} else {
					x++;
				}
			}
		}
	});
});

