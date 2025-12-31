/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools"
], function(lang, array, tools) {
	// helper function also used by wizard. Needs to defined here to be accessible by setNetwork
	var _setNetworkValues = function(vals, widgets) {
		widgets.ip.set('value', [vals.ip]);
		widgets.dnsEntryZoneForward.set('value', [[vals.dnsEntryZoneForward, vals.ip]]);
		widgets.dnsEntryZoneReverse.set('value', [[vals.dnsEntryZoneReverse, vals.ip]]);
		if (vals.mac.length && vals.dhcpEntryZone) {
			// at least one MAC address is specified, update the DHCP entries
			widgets.dhcpEntryZone.set('value', [[vals.dhcpEntryZone, vals.ip, vals.mac[0]]]);
		} else if (vals.dhcpEntryZone) {
			// no MAC address given, enter the DHCP entry and make sure that the MAC
			// is chosen as soon as it is specified later on (via 'null' value)
			widgets.dhcpEntryZone.set('value', [[vals.dhcpEntryZone, vals.ip, null]]);
		} else {
			// DHCP entry zone does not exist
			widgets.dhcpEntryZone.set('value', []);
		}
	};

	return {
		setDynamicValues: function(dict) {
			// return the list specified by the property '$depends$'
			// make sure that elements do not exist twice
			var tmpMap = {};
			var list =  array.filter(dict[dict.$depends$], function(ival) {
				if (!(ival in tmpMap)) {
					tmpMap[ival] = true;
					return true;
				}
				return false;
			});
			if ( dict.$depends$ == 'dnsEntryZoneForward' ) {
				list = array.map( list, function( item ) {
					return tools.explodeDn( item[ 0 ], true )[ 0 ];
				} );
			}
			return list;
		},

		setNetwork: function(newVal, widgets) {
			if (!lang.getObject('network.focused', false, widgets)) {
				// only react on user changes of the network
				return;
			}

			// query a new IP address and update network configurations automatically...
			if (!newVal || newVal == 'None') {
				// empty list
				widgets.ip.set('value', []);
				widgets.dnsEntryZoneForward.set('value', []);
				widgets.dnsEntryZoneReverse.set('value', []);
				widgets.dhcpEntryZone.set('value', []);
			}
			else {
				tools.umcpCommand('udm/network', {
					networkDN: newVal
				}, true, 'computers/computer').then(lang.hitch(this, function(data) {
					// got values... update corresponding widgets
					var vals = lang.mixin(data.result, {mac: widgets.mac.get('value')});
					_setNetworkValues(vals, widgets);
				}));
			}
		},

		_setNetworkValues: _setNetworkValues
	};
});



