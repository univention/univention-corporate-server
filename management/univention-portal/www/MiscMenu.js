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
	"dojo/Deferred",
	"umc/widgets/ContainerWidget",
	"./_Menu",
	"umc/i18n!"
], function(declare, Deferred, ContainerWidget, PortalMenu, _) {

	var miscMenuDeferred = new Deferred();

	var MiscMenu = declare('portal.MiscMenu', [PortalMenu], {
		postMixInProperties: function() {
			this.inherited(arguments);
			this.$wrapper = new ContainerWidget({});
		},

		postCreate: function() {
			this.inherited(arguments);
			if (miscMenuDeferred.isResolved()) {
				console.warn('MiscMenu created twice: only the first created MiscMenu gets the subsequently added menu entries (like from univention-web/js/hooks/default_menu_entries.js). The MiscMenu was not intended to exist more than once');
			} else {
				miscMenuDeferred.resolve(this);
			}
		}
	});

	MiscMenu.addItem = function(conf) {
		miscMenuDeferred.then(function(miscMenu) {
			miscMenu.addItem(conf);
		});
	};

	return MiscMenu;
});

