/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
							}),
							'class': 'umcTextBoxOnBody'
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
							}),
							'class': 'umcTextBoxOnBody'
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
							onSearch: lang.hitch(this, 'submit'),
							'class': 'umcTextBoxOnBody'
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
