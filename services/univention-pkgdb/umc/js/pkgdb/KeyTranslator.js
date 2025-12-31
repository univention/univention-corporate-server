/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
