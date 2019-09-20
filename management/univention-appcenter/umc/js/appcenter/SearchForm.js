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
/*global define console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/tools",
	"umc/widgets/Form",
	"umc/widgets/ComboBox",
	"umc/widgets/SearchBox",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, tools, Form, ComboBox, SearchBox, _) {
	return declare("umc.modules.appcenter.SearchForm", [ Form ], {

		postMixInProperties: function() {

			try {
				lang.mixin(this, {
					widgets:
					[
						{
							name: 'section',
							label: _("Package categories"),
							size: 'TwoThirds',
							type: ComboBox,
							staticValues: [{ id: 'all', label: _("--- all ---") }],
							sortStaticValues: false,
							dynamicValues: 'appcenter/packages/sections',
							onDynamicValuesLoaded: lang.hitch(this, function() {
								this.allowSearchButton(true);
							}),
							sortDynamicValues: false,
							onChange: lang.hitch(this, function() {
								this._check_submit_allow();
							})
						},
						{
							name: 'key',
							label: _("Search key"),
							size: 'TwoThirds',
							type: ComboBox,
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
							inlineLabel: _('Search...'),
							size: 'TwoThirds',
							type: SearchBox,
							value: '*',
							required: false,
							onChange: lang.hitch(this, function() {
								this._check_submit_allow();
							}),
							onSearch: lang.hitch(this, 'submit')
						}
					],
					layout:
					[
						['section', 'key', 'pattern']
					]
				});
			} catch(error) {
				console.error("SearchForm::postMixInProperties() ERROR: " + error.message);
			}
			this.inherited(arguments);
		},

		_check_submit_allow: function() {

			var allow = true;
			tools.forIn(this._widgets, function(iname, iwidget) {
				if (! iwidget.isValid()) {
					allow = false;
				}
			});

			this.allowSearchButton(allow);
		},

		// while a query is pending the search button should be disabled. This function
		// is called from inside (onSubmit) and from outside (in the onFetchComplete
		// callback of the grid)
		allowSearchButton: function(yes) {
			this._buttons.submit.set('disabled', !yes);
			this._widgets.pattern.set('disabled', !yes);
			this._widgets.pattern.focus();
		},

		onSubmit: function() {
			this.allowSearchButton(false);
			return this.inherited(arguments);
		}
	});
});
