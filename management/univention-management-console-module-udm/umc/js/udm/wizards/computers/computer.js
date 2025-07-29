/*
 * SPDX-FileCopyrightText: 2013-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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

