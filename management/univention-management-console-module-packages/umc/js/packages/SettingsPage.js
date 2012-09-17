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
	"dojo/_base/lang",
	"umc/dialog",
	"umc/modules/packages/store",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/StandbyMixin",
	"umc/modules/packages/Form",
	"umc/i18n!umc/modules/packages"
], function(declare, lang, dialog, store, tools, Page, StandbyMixin, Form, _) {
	return declare("umc.modules.packages.SettingsPage", [ Page, StandbyMixin ], {

		postMixInProperties: function() {
			this.inherited(arguments);

			lang.mixin(this, {
				title: _("Settings"),
				headerText: _("Settings for online updates"),
				helpText: _("This page lets you modify essential settings that affect where your system looks for updates, and which of them it will consider."),
				footerButtons:
				[
					{
						name: 'reset',
						label: _('Reset'),
						onClick: lang.hitch(this, function() {
							this._form.load({}); // ID doesn't matter here but must be dict
							tools.forIn(this._form._widgets, function(iname, iwidget) {
								iwidget.setValid(true);
							});
						})
					},
					{
						name: 'submit',
						'default': true,
						label: _("Apply changes"),
						onClick: lang.hitch(this, function() {
							this.standby(true);
							this._form.save();
						})
					}
				]
			});
		},

		buildRendering: function() {

			this.inherited(arguments);

			var widgets =
			[
				{
					type: 'TextBox',
					name: 'server',
					label: _("Repository server")
				},
				{
					type: 'TextBox',
					name: 'prefix',
					label: _("Repository prefix")
				},
				{
					type: 'CheckBox',
					name: 'maintained',
					label: _("Use maintained repositories")
				},
				{
					type: 'CheckBox',
					name: 'unmaintained',
					label: _("Use unmaintained repositories")
				}
			];

			var layout =
			[
				{
					label: _("Update-related settings"),
					layout:
					[
						['server', 'prefix'],
						['maintained', 'unmaintained']
					]
				}
			];
		
			this._form = new Form({
				widgets: widgets,
				layout: layout,
				//buttons: buttons,
				moduleStore: store('server', 'packages/settings'),
				scrollable: true,
				onSaved: lang.hitch(this, function(success, data) {
					this.standby(false);
					if (success) {
						// this is only Python module result, not data validation result!
						var result = data;
						if (data instanceof Array) {
							result = data[0];
						}
						if (result.status) {
							if (result.message) {
								// result['status'] is kind of error code:
								//	1 ... invalid field input
								//	2 ... error setting registry variable
								//	3 ... error commiting UCR
								//	4 ... any kind of 'repo not found' conditions
								//	5 ... repo not found, but encountered without commit
								var txt = _("An unknown error with code %d occured.", result.status);
								switch(result.status) {
									case 1: txt = _("Please correct the corresponding input fields:");
											break;
									case 2:
									case 3: txt = _("The data you entered could not be saved correctly:");
											break;
									case 4: txt = _("Using the data you entered, no valid repository could be found.<br/>Since this may be a temporary server problem as well, your data was saved though.<br/>The problem was:");
											break;
									case 5: txt = _("With the current (already changed) settings, the following problem was encountered:");
											break;
								}
		
								var message = lang.replace('<p>{txt}</p><p><strong>{msg}</strong></p>', {txt : txt, msg : result.message});
		
								dialog.alert(message);
							}
						}
					}
				})
			});
			this.addChild(this._form);

			this._form.on('submit', lang.hitch(this, function() {
				this.standby(true);
				this._form.save();
			}));

			this._form.load({}); // ID doesn't matter here but must be dict
		},

		// Let's fetch the current values again directly before we show the form.
		onShow: function() {
			this._form.load({}); // ID doesn't matter here but must be dict
		}

	});
});
