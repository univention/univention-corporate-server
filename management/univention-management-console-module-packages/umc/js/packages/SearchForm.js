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
/*global define console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/modules/packages/Form",
	"umc/i18n!umc/modules/packages"
], function(declare, lang, Form, _) {
	return declare("umc.modules.packages.SearchForm", [ Form ], {

		postMixInProperties: function() {

			try {
				lang.mixin(this, {
					widgets:
					[
						{
							name: 'section',
							label: _("Package categories"),
							type: 'ComboBox',
							staticValues: [{ id: 'all', label: _("--- all ---") }],
							sortStaticValues: false,
							required: true,
							dynamicValues: 'packages/sections',
							onDynamicValuesLoaded: lang.hitch(this, function() {
								this.allowSearchButton(true);
							}),
							sortDynamicValues: false,
							onChange: lang.hitch(this, function() {
								this._check_submit_allow();
							})
						},
						{
							name: 'installed',
							label: _("Installed packages only"),
							type: 'CheckBox'
	// doesn't make sense: a Bool on its own is always valid.
	//						onChange: lang.hitch(this, function() {
	//							this._check_submit_allow();
	//						})
						},
						{
							name: 'key',
							label: _("Search key"),
							type: 'ComboBox',
							staticValues: [
						 { id: 'package',		label: _("Package name") },
						 { id: 'description',	label: _("Package description") }
							],
							sortStaticValues: false,
							onChange: lang.hitch(this, function() {
								this._check_submit_allow();
							})
						},
						{
							name: 'pattern',
							label: _("Pattern"),
							type: 'TextBox',
							value: '*',
							required: false,
							onChange: lang.hitch(this, function() {
								this._check_submit_allow();
							})
						}
					],
					buttons:
					[
						{
							name: 'submit',
							label: _("Search")
						}
					],
					layout:
					[
						['installed'],
						['section'],
						['key', 'pattern', 'submit']
					]
				});
			} catch(error) {
				console.error("SearchForm::postMixInProperties() ERROR: " + error.message);
			}
			this.inherited(arguments);
		},

		_check_submit_allow: function() {

			var allow = true;
			for (var w in this._widgets) {
				if (w != 'installed')	// workaround for ComboBox
				{
					if (! this._widgets[w].isValid())
					{
						allow = false;
					}
				}
			}

			this.allowSearchButton(allow);
		},
		//
		// while a query is pending the search button should be disabled. This function
		// is called from inside (onSubmit) and from outside (in the onFetchComplete
		// callback of the grid)
		allowSearchButton: function(yes) {
			this._buttons.submit.set('disabled', !yes);
		},

		onSubmit: function() {
			this.allowSearchButton(false);
		}

	});
});
