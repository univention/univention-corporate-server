/*
 * Copyright 2011-2012 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"umc/modules/pkgdb/Page",
	"umc/widgets/TabbedModule",
	"umc/i18n!umc/modules/pkgdb"
], function(declare, Page, TabbedModule, _) {
	return declare("umc.modules.pkgdb", [ TabbedModule ], {

		buildRendering: function() {
			this.inherited(arguments);

			var syspage = new Page({
				title:			_("Systems"),
				headerText:		_("Search systems"),
				helpText:		_("Search for systems with specific software properties"),
				pageKey:		'systems'
			});
			this.addChild(syspage);

			var packpage = new Page({
				title:			_("Packages"),
				headerText:		_("Search packages"),
				helpText:		_("Search for packages with specific software properties"),
				pageKey:		'packages'
			});
			this.addChild(packpage);

			var propage = new Page({
				title:			_("Problems"),
				headerText:		_("Identify problems"),
				helpText:		_("Find problems related to software package installation"),
				pageKey:		'problems'
			});
			this.addChild(propage);
			
		}
	});
});
