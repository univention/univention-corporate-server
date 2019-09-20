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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/window",
	"dojo/window",
	"dojo/dom-class",
	"dojo/Evented",
	"umc/tools",
	"umc/menu/Menu",
	"umc/menu/Button"
], function(declare, lang, baseWin, win, domClass, Evented, tools, Menu, Button) {
	var menu = new declare([Evented], {
		addSubMenu: function(/*Object*/ item) {
			return this.getMenuInstance().then(function(menu) {
				return menu.addSubMenu(item);
			});
		},

		addEntry: function(/*Object*/ item) {
			return this.getMenuInstance().then(function(menu) {
				return menu.addMenuEntry(item);
			});
		},

		addSeparator: function(/*Object*/ item) {
			return this.getMenuInstance().then(function(menu) {
				return menu.addMenuSeparator(item);
			});
		},

		createMenu: function(props) {
			props = props || {};
			return new Menu(props);
		},

		open: function() {
			domClass.toggle(baseWin.body(), 'mobileMenuActive');
			var hasScrollbar = baseWin.body().scrollHeight > win.getBox().h;
			domClass.toggle(baseWin.body(), 'hasScrollbar', hasScrollbar);
			tools.defer(function() {
				domClass.toggle(baseWin.body(), 'mobileMenuToggleButtonActive');
			}, 510);
		},

		close: function() {
			if (!domClass.contains(baseWin.body(), 'mobileMenuActive')) {
				return;
			}
			domClass.remove(baseWin.body(), 'mobileMenuActive');
			domClass.remove(baseWin.body(), 'hasScrollbar');
			tools.defer(lang.hitch(this, function() {
				domClass.toggle(baseWin.body(), 'mobileMenuToggleButtonActive');

				this.getMenuInstance().then(function(menuInstance) {
					menuInstance.closeOpenedSubMenus();
				});
			}), 510);
		},

		getButtonInstance: function() {
			return Button.menuButtonDeferred;
		},

		getMenuInstance: function() {
			return Menu.mobileMenuDeferred;
		},

		hideEntry: function(entryDeferred) {
			entryDeferred.then(function(entry) {
				entry.hide();
			});
		},

		showEntry: function(entryDeferred) {
			entryDeferred.then(function(entry) {
				entry.show();
			});
		}
	})();
	return menu;
});
