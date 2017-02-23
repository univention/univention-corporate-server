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
/*global define,require,console,setTimeout,window,document*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/Evented",
	"umc/widgets/Menu"
], function(declare, lang, Evented, Menu) {
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

		getButtonInstance: function() {
			return Menu.menuButtonDeferred;
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
