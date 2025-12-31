/*
 * SPDX-FileCopyrightText: 2012-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, _) {
	var self = {
		convertNetmask: function(nm) {
			// 255.255.255.0 -> 24
			if (/^[0-9]+$/.test(nm)) {
				return parseInt(nm, 10);
			}
			var num = 0;
			array.forEach(nm.split('.'), function(i) {
				i = parseInt(i, 10);
				for (;i> 0; i = (i <<1) % 256) {
					num++;
				}
			});

			return num;
		},
		interfaceTypeLabels: {
			'Ethernet': _('Ethernet'),
			'VLAN': _('Virtual LAN'),
			'Bond': _('Bonding'),
			'Bridge': _('Bridge')
		}
	};

	return self;
});
