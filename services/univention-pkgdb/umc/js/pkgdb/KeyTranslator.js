/*
 * Copyright 2011-2019 Univention GmbH
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
	"umc/i18n!umc/modules/pkgdb"
], function(declare, _) {
	// A helper mixin that is mixed into any instance of our umc.modules.pkgdb.Page class.
	// Helps with i18n issues.
	return declare("umc.modules.pkgdb.KeyTranslator", [], {

		// This function accepts a field (column) name and returns any additional
		// options that are needed in construction of the data grid. Even if all
		// structural information is kept in the Python module, the design properties
		// of the frontend should be concentrated in the JS part.
		_field_options: function(key) {

			var t = {
				'inststate': {
					label: _("Installation state"),
					width: 'adjust'
				},
				'inventory_date': {
					label: _("Inventory date")
				},
				'pkgname': {
					label: _("Package name")
				},
				'vername': {
					label: _("Package version")
				},
				'currentstate': {
					label: _("Package state"),
					width: 'adjust'
				},
				'selectedstate': {
					label: _("Selection state"),
					width: 'adjust'
				},
				'sysname': {
					label: _("Hostname")
				},
				'sysrole': {
					label: _("System role")
				},
				'sysversion': {
					label: _("UCS version")
				}
			};

			return t[key] || null;
		}

	});
});
