/*
 * Copyright 2013-2019 Univention GmbH
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
	"umc/modules/udm/callbacks",
	"umc/modules/udm/wizards/CreateWizard",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, udmCallbacks, CreateWizard, _) {

	return declare("umc.modules.udm.wizards.computers.computer", [ CreateWizard ], {
		widgetPages: [
			{
				widgets: [
					['name'],
					['network'],
					['mac', 'ip']
				]
			}
		],

		buildWidget: function(widgetName, originalWidgetDefinition) {
			var widget = this.inherited(arguments);
			if (widgetName == 'network') {
				widget.type = 'ComboBox'; // not UDMComboBox
				widget.umcpCommand = this.umcpCommand;
				widget.dynamicValues = 'udm/syntax/choices';
				widget.dynamicOptions = {'syntax' : 'network'};
				widget.onChange = lang.hitch(this, function(newVal, widgets) {
					if (newVal) {
						this.umcpCommand('udm/network', {networkDN: newVal}).then(lang.hitch(this, function(data) {
							this._networkVals = data.result;
							widgets.ip.set('value', this._networkVals.ip);
						}));
					} else {
						this._networkVals = null;
					}
				});
			}
			return widget;
		},

		setCustomValues: function(values, detailPageForm) {
			if (this._networkVals && values.ip[0]) {
				var vals = lang.mixin({}, this._networkVals, {ip: values.ip[0], mac: values.mac});
				if (vals.mac[0] === '') {
					vals.mac = [];
					vals.dhcpEntryZone = null;
				}
				udmCallbacks._setNetworkValues(vals, detailPageForm._widgets);
			}
		}

	});
});

