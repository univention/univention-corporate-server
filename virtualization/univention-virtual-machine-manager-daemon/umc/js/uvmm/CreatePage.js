/*
 * Copyright 2014-2020 Univention GmbH
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
	"dojo/_base/array",
	"dojo/promise/all",
	"umc/tools",
	"umc/widgets/Wizard",
	"umc/widgets/ComboBox",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, all, tools, Wizard, ComboBox, types, _) {

	return declare("umc.modules.uvmm.CreatePage", [ Wizard ], {
		umcpCommand: null,
		item: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			var _getNodes = lang.hitch(this, function() {
				var deferreds = [];
				deferreds.push(this.umcpCommand('uvmm/node/query'));

				return all(deferreds).then(lang.hitch(this, function(results) {
					var servers = [];
					array.forEach(results, lang.hitch(this, function(iresult) {
						array.forEach(iresult.result, lang.hitch(this, function(iserver) {
							if (tools.isTrue(iserver.available)) {
								if (this.item && iserver.label.indexOf(this.item.label) === 0) {
									iserver.preselected = true;
								}
								servers.push(iserver);
							}
						}));
					}));
					return servers;
				}));
			});

			lang.mixin(this, {
				headerText: _('Create a virtual machine'),
				helpText: _('Select the server where a new virtual machine instance is going to be created.'),
				headerButtons: [{
					name: 'close',
					iconClass: 'umcCloseIconWhite',
					label: _('Back to overview'),
					callback: lang.hitch(this, 'onCancel')
				}],
				footerButtons: [{
					label: _('Next'),
					defaultButton: true,
					name: 'next',
					callback: lang.hitch(this, '_finish')
				}],
				pages: [{
					headerText: _('Create a virtual machine'),
					helpText: _('Create a new virtual machine instance.'),
						type: ComboBox,
						name: 'server',
						dynamicValues: _getNodes,
						onDynamicValuesLoaded: lang.hitch(this, function(values) {
							if (values.length === 0) {
								this.getWidget('server').set('visible', false);
							}
						}),
						label: _('Where should the virtual machine instance be created'),
						labelConf: {'style': 'margin-left: 27px;'}
				}]
			});
		},

		_getSelectedServer: function() {
			var serverID = this.getWidget('server').get('value');
			var server = array.filter(this.getWidget('server').getAllItems(), function(item) {
				return item.id == serverID;
			});
			if (!server.length) {
				return null;
			}
			return server[0];
		},

		getValues: function() {
			// save the type that shall be created
			var server = this._getSelectedServer();
			var values = {
				type: 'domain',
				nodeURI: server.id
			};
			return values;
		},

		getFooterButtons: function() {
			var buttons = this.inherited(arguments);
			return array.map(buttons, function(button) {
				if (button.name == 'finish') {
					button.label = _('Next');
				}
				return button;
			});
		},

		_finish: function() {
			// trigger finished event
			this.onFinished(this.getValues());
		}
	});
});
