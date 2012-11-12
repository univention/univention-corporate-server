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
	"dojo/_base/array",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Page",
	"umc/widgets/StandbyMixin",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/widgets/MultiInput",
	"umc/widgets/MultiSelect",
	"umc/widgets/Form",
	"umc/widgets/Button",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, tools, dialog, Page, StandbyMixin, TextBox, ComboBox, MultiInput, MultiSelect, Form, Button, _) {
	return declare("umc.modules.setup.NetworkPage", [ Page, StandbyMixin ], {
		// summary:
		//		This class renderes a detail page containing subtabs and form elements
		//		in order to edit UDM objects.

		// system-setup-boot
		wizard_mode: false,

		// __systemsetup__ user is logged in at local firefox session
		local_mode: false,

		umcpCommand: tools.umcpCommand,

		// internal reference to the formular containing all form widgets of an UDM object
		_form: null,

		// dicts of the original IPv4/v6 values
		_orgValues: null,

		_noteShowed: false,

		_currentRole: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			this.title = _('Network');
			this.headerText = _('Network settings');
			this.helpText = _('In the <i>network settings</i>, IP addresses (IPv4 and IPv6) as well as name servers, gateways, and HTTP proxies may be specified.');
		},

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: MultiInput,
				name: 'interfaces_ipv4',
				label: '', //_('Interfaces'),
				umcpCommand: this.umcpCommand,
				subtypes: [{
					type: ComboBox,
					label: _('Interface'),
					dynamicValues: lang.hitch(this, function() {
						return this.umcpCommand('setup/net/interfaces').then(lang.hitch(this, function(data) {
							// for ipv4 interfaces, we can have a virtual one, as well
							var list = [];
							array.forEach(data.result, function(idev) {
								var idev2 = {
									id: idev + '_virtual',
									label: idev + ' (' + _('virtual') + ')'
								};
								list.push(idev, idev2);
							}, this);
							return list;
						}));
					}),
					sizeClass: 'OneThird'
				}, {
					type: TextBox,
					label: _('IPv4 address'),
					sizeClass: 'Half'
				}, {
					type: TextBox,
					label: _('Netmask'),
					sizeClass: 'Half'
				}, {
					type: ComboBox,
					label: _('Dynamic (DHCP)'),
					staticValues: [
						{ id: 'false', label: _('Deactivated') },
						{ id: 'true', label: _('Activated') }
					],
					sizeClass: 'OneThird'
				}, {
					type: Button,
					label: 'DHCP query',
					callback: lang.hitch(this, '_dhcpQuery')
				}]
			}, {
				type: MultiInput,
				name: 'interfaces_ipv6',
				label: '', //_('Interfaces'),
				umcpCommand: this.umcpCommand,
				subtypes: [{
					type: ComboBox,
					label: _('Interface'),
					dynamicValues: 'setup/net/interfaces',
					sizeClass: 'OneThird'
				}, {
					type: TextBox,
					label: _('IPv6 address'),
					sizeClass: 'One'
				}, {
					type: TextBox,
					label: _('IPv6 prefix'),
					sizeClass: 'OneThird'
				}, {
					type: TextBox,
					label: _('Identifier'),
					sizeClass: 'OneThird'

				}]
			}, {
				type: MultiSelect,
				name: 'dynamic_interfaces_ipv6',
				label: _('Autoconfiguration (SLAAC)'),
				umcpCommand: this.umcpCommand,
				dynamicValues: 'setup/net/interfaces',
				autoHeight: true,
				sizeClass: 'OneThird'
			}, {
				type: TextBox,
				name: 'gateway',
				label: _('Gateway (IPv4)')
			}, {
				type: TextBox,
				name: 'ipv6/gateway',
				label: _('Gateway (IPv6)')
			}, {
				type: MultiInput,
				subtypes: [{ type: TextBox }],
				name: 'nameserver',
				label: _('Domain name server (max. 3)'),
				max: 3
			}, {
				type: MultiInput,
				subtypes: [{ type: TextBox }],
				name: 'dns/forwarder',
				label: _('External name server (max. 3)'),
				max: 3
			}, {
				type: TextBox,
				name: 'proxy/http',
				label: _('HTTP proxy')
			}];

			var layout = [{
				label: _('IPv4 network devices'),
				layout: ['interfaces_ipv4']
			}, {
				label: _('IPv6 network devices'),
				layout: ['interfaces_ipv6', 'dynamic_interfaces_ipv6']
			}, {
				label: _('Global network settings'),
				layout: [ ['gateway', 'ipv6/gateway'], 'nameserver', 'dns/forwarder', 'proxy/http']
			}];

			this._form = new Form({
				widgets: widgets,
				layout: layout,
				scrollable: true
			});
			this._form.on('submit', lang.hitch(this, 'onSave'));

			// add onChange handlers that show the note
			array.forEach(['interfaces_ipv4', 'interfaces_ipv6'], function(iname) {
				var iwidget = this._form.getWidget(iname);
				this.own(iwidget.watch('value', lang.hitch(this, function() {
					if (iwidget.focused) {
						this._showNote();
					}
				})));
			}, this);
			
			this.addChild(this._form);
		},

		_showNote: function() {
			if (!this._noteShowed) {
				this._noteShowed = true;
				this.addNote(_('Changing IP address configurations may result in restarting or stopping services. This can have severe side-effects when the system is in productive use at the moment.'));
			}
		},

		_dhcpQuery: function(item, idx) {
			// switch on standby animation
			this.standby(true);

			// make sure we have an interface selected
			if (!item || !item[0] || typeof item[0] != "string") {
				dialog.alert(_('Please choose a network device before querying a DHCP address.'));
				this.standby(false);
				return;
			}
			if (item[0].indexOf('_virtual') >= 0) {
				dialog.alert(_('A virtual network device cannot be used for DHCP.'));
				this.standby(false);
				return;
			}
			this.umcpCommand('setup/net/dhclient', {
				'interface': item[0]
			}).then(lang.hitch(this, function(data) {
				// switch off standby animation
				this.standby(false);

				var result = data.result;
				var netmask = result[item[0] + '_netmask'];
				var address = result[item[0] + '_ip'];
				if (!address && !netmask) {
					dialog.alert(_('DHCP query failed.'));
					return;
				}

				// set the queried IP and netmask
				var devicesWidget = this._form.getWidget('interfaces_ipv4');
				var val = devicesWidget.get('value');
				if (address) {
					val[idx][1] = address;
				}
				if (netmask) {
					val[idx][2] = netmask;
				}
				// set "Dynamic (DHCP)" to be false if it was not set
				if ( val[idx][3] === '') {
					val[idx][3] = 'false';
				}

				// set gateway
				devicesWidget.set('value', val);
				if (result.gateway) {
					var gatewayWidget = this._form.getWidget('gateway');
					gatewayWidget.set('value', result.gateway);
				}

				// read nameserver or dns/forwarder
				var nameserverWidget;
				if (this._form.getWidget('nameserver').get('visible')) {
					nameserverWidget = this._form.getWidget('nameserver');
				} else {
					// if nameserver is not visable, set dns/forwarder
					nameserverWidget = this._form.getWidget('dns/forwarder');
				}
				val = nameserverWidget.get('value');
				if (result.nameserver_1) {
					val[0] = result.nameserver_1;
				}
				if (result.nameserver_2) {
					val[1] = result.nameserver_2;
				}
				if (result.nameserver_3) {
					val[2] = result.nameserver_3;
				}
				nameserverWidget.set('value', val);

			}), lang.hitch(this, function() {
				// switch off standby animation
				this.standby(false);
			}));
		},

		sortInterfaces: function(x, y) {
			if (x.id != y.id) {
				// this is for ipv6 types, the id 'default' should be listed as first device
				if (x.id == 'default') {
					return 1;
				}
				if (y.id == 'default') {
					return -1;
				}
			}
			// virtual devices should be listed below
			if (x.virtual !== y.virtual) {
				return x.virtual ? -1 : 1;
			}
			// otherwise sort according to device name (virtual as well as non-virtual ones)
			if (x.device > y.device) {
				return 1;
			}
			if (x.device < y.device) {
				return -1;
			}
			return 0;
		},
			
		setValues: function(_vals) {
			// save a copy of all original values that may be lists
			var r = /^(interfaces\/[^\/]+\/|nameserver[1-3]|dns\/forwarder[1-3])$/;
			this._orgValues = {};
			tools.forIn(_vals, function(ikey, ival) {
				if (r.test(ikey)) {
					this._orgValues[ikey] = ival;
				}
			}, this);

			// copy values that do not change in their name
			var vals = {};
			array.forEach(['gateway', 'ipv6/gateway', 'proxy/http'], function(ikey) {
				vals[ikey] = _vals[ikey];
			});

			// sort the keys such that the interface order is correct
			var sortedKeys = [];
			tools.forIn(_vals, function(ikey) {
				sortedKeys.push(ikey);
			});
			sortedKeys.sort();

			// copy lists of nameservers/forwarders
			vals.nameserver = [];
			vals['dns/forwarder'] = [];
			array.forEach(sortedKeys, function(ikey) {
				array.forEach(['nameserver', 'dns/forwarder'], function(jname) {
					if (0 === ikey.indexOf(jname)) {
						vals[jname].push(_vals[ikey]);
					}
				});
			});

			// copy ipv4 interfaces
			r = /interfaces\/(([^_\/]+)(_([0-9]+))?)\/(.+)/;
			var ipv4 = {};
			array.forEach(sortedKeys, function(ikey) {
				var match = ikey.match(r);
				if (_vals[ikey] && match) {
					var iname = match[1];
					var idev = match[2];
					var ivirtual = parseInt(match[4], 10);
					var type = match[5];
					ipv4[iname] = ipv4[iname] ? ipv4[iname] : {};
					ipv4[iname][type] = _vals[ikey];
					ipv4[iname].virtual = !isNaN(ivirtual);
					ipv4[iname].device = idev;
				}
			});

			// get the correct order (real interfaces first, then virtual ones)
			var sortedIpv4 = [];
			tools.forIn(ipv4, function(ikey, ival) {
				sortedIpv4.push(ival);
			});

			// translate to our datastructure
			vals.interfaces_ipv4 = [];
			array.forEach(sortedIpv4, function(idev) {
				vals.interfaces_ipv4.push([
					idev.virtual ? idev.device + '_virtual' : idev.device,
					idev.address || '',
					idev.netmask || '',
					idev.type == 'dynamic' || idev.type == 'dhcp' ? 'true' : 'false'
				]);
			});

			// copy ipv6 interfaces
			r = /interfaces\/([^\/]+)\/ipv6\/([^\/]+)\/(.+)/;
			var ipv6 = {};
			array.forEach(sortedKeys, function(ikey) {
				var match = ikey.match(r);
				if (_vals[ikey] && match) {
					var idev = match[1];
					var iid = match[2];
					var type = match[3];
					var iname = idev + '/' + iid;
					ipv6[iname] = ipv6[iname] ? ipv6[iname] : {};
					ipv6[iname][type] = _vals[ikey];
					ipv6[iname].id = iid;
					ipv6[iname].device = idev;
				}
			});

			// get the correct order (real interfaces first, then virtual ones)
			var sortedIpv6 = [];
			tools.forIn(ipv6, function(ikey, ival) {
				sortedIpv6.push(ival);
			});
			sortedIpv6.sort(this.sortInterfaces);

			// translate to our datastructure
			vals.interfaces_ipv6 = [];
			array.forEach(sortedIpv6, function(idev) {
				vals.interfaces_ipv6.push([
					idev.device,
					idev.address || '',
					idev.prefix || '',
					idev.id || ''
				]);
			});

			// dynamic ipv6 interfaces
			r = /interfaces\/([^\/]+)\/ipv6\/acceptRA/;
			vals.dynamic_interfaces_ipv6 = [];
			array.forEach(sortedKeys, function(ikey) {
				var match = ikey.match(r);
				if (tools.isTrue(_vals[ikey]) && match) {
					vals.dynamic_interfaces_ipv6.push(match[1]);
				}
			});

			// only show forwarder for master, backup, and slave
			this._currentRole = _vals['server/role'];
			var showForwarder = this._currentRole == 'domaincontroller_master' || this._currentRole == 'domaincontroller_backup' || this._currentRole == 'domaincontroller_slave';
			this._form.getWidget('dns/forwarder').set('visible', showForwarder);

			// hide domain nameserver on master when using system setup boot
			this._form.getWidget('nameserver').set('visible', ! ( this.wizard_mode && this._currentRole == 'domaincontroller_master' ) );
			// set values
			this._form.setFormValues(vals);

			// only show notes in an joined system in productive mode
			this._noteShowed = this.wizard_mode;
			this.clearNotes();
		},

		getValues: function() {
			var _vals = this._form.gatherFormValues();
			var vals = {};

			// copy values that do not change in their name
			array.forEach(['gateway', 'ipv6/gateway', 'proxy/http'], function(ikey) {
				vals[ikey] = _vals[ikey];
			});

			// copy lists of nameservers/forwarders
			array.forEach(['nameserver', 'dns/forwarder'], function(iname) {
				array.forEach(_vals[iname], function(jval, j) {
					vals[iname + (j + 1)] = jval;
				});
			});

			// copy ipv4 interfaces
			var iipv4Virtual = {};  // counter for the virtual interfaces
			array.forEach(_vals.interfaces_ipv4, function(ival) {
				var idev = ival[0];
				var iaddress = ival[1];
				var imask = ival[2];
				var idynamic = ival[3] == 'true';
				var iname = idev;
				if (iname.indexOf('_virtual') >= 0) {
					if (!(idev in iipv4Virtual)) {
						// first virtual interfaces for this device
						iipv4Virtual[idev] = 0;
					}
					iname = iname.replace('virtual', iipv4Virtual[idev]);
					++iipv4Virtual[idev]; // count up the number of virtual interfaces for this device
				}
				else {
					// only real interfaces may use DHCP
					if (idynamic) {
						vals['interfaces/' + iname + '/type'] = 'dynamic';
					}
				}
				vals['interfaces/' + iname + '/address'] = iaddress;
				vals['interfaces/' + iname + '/netmask'] = imask;
			});

			// copy ipv6 interfaces
			array.forEach(_vals.interfaces_ipv6, function(ival) {
				var idev = ival[0];
				var iaddress = ival[1];
				var iprefix = ival[2];
				var iid = ival[3];
				vals['interfaces/' + idev + '/ipv6/' + iid + '/address'] = iaddress;
				vals['interfaces/' + idev + '/ipv6/' + iid + '/prefix'] = iprefix;
			});

			// dynamic ipv6 interfaces
			//array.forEach(_vals.dynamic_interfaces_ipv6, function(idev) {
			array.forEach(this._form.getWidget('dynamic_interfaces_ipv6').getAllItems(), function(iitem) {
				vals['interfaces/' + iitem.id + '/ipv6/acceptRA'] = (array.indexOf(_vals.dynamic_interfaces_ipv6, iitem.id) >= 0) ? 'true' : 'false';
			});

			// add empty entries for all original entries that are not used anymore
			tools.forIn(this._orgValues, function(ikey, ival) {
				if (!(ikey in vals)) {
					vals[ikey] = '';
				}
			});

			return vals;
		},

		getSummary: function() {
			// a list of all components with their labels
			var allInterfaces = {};
			array.forEach(this._form.getWidget('dynamic_interfaces_ipv6').getAllItems(), function(iitem) {
				allInterfaces[iitem.id] = iitem.label;
				allInterfaces[iitem.id + '_virtual'] = iitem.label + ' [' + _('virtual') + ']';
			}, this);

			// list of all IPv4 network devices
			var vals = this._form.gatherFormValues();
			var ipv4Str = '<ul>';
			array.forEach(vals.interfaces_ipv4, function(idev) {
				if (idev[1]) {
					// address is given
					ipv4Str += '<li>' +
							idev[1] + '/' + idev[2] +
							' (' +
								allInterfaces[idev[0]] +
								(idev[3] == 'true' ? ', DHCP' : '') +
							')</li>';
				} else {
					// address is not given: must be DHCP
					ipv4Str += '<li>' +
							allInterfaces[idev[0]] + ': DHCP' +
							'</li>';
				}
			});
			ipv4Str += '</ul>';

			// list of all IPv6 network devices
			var ipv6Str = '<ul>';
			array.forEach(vals.interfaces_ipv6, function(idev) {
				ipv6Str += '<li>' +
						idev[1] + ' - ' + idev[2] + '/' + idev[3] +
						' (' + idev[0] + ')</li>';
			});
			ipv6Str += '</ul>';

			// create a verbose list of all settings
			return [{
				variables: ['gateway'],
				description: _('Gateway (IPv4)'),
				values: vals['gateway']
			}, {
				variables: ['ipv6/gateway'],
				description: _('Gateway (IPv6)'),
				values: vals['ipv6/gateway']
			}, {
				variables: [/nameserver.*/],
				description: _('Domain name server'),
				values: vals['nameserver'].join(', ')
			}, {
				variables: [/dns\/forwarder.*/],
				description: _('External name server'),
				values: vals['dns/forwarder'].join(', ')
			}, {
				variables: ['proxy/http'],
				description: _('HTTP proxy'),
				values: vals['proxy/http']
			}, {
				variables: [/^interfaces\/[^_\/]+(_[0-9]+)?\/(?!ipv6).*/],
				description: _('IPv4 network devices'),
				values: ipv4Str
			}, {
				variables: [/^interfaces\/[^\/]+\/ipv6\/.*\/(prefix|address)$/],
				description: _('IPv6 network devices'),
				values: ipv6Str
			}, {
				variables: [/^interfaces\/[^\/]+\/ipv6\/acceptRA/],
				description: _('IPv6 interfaces with autoconfiguration (SLAAC)'),
				values: vals['dynamic_interfaces_ipv6'].length ? vals['dynamic_interfaces_ipv6'].join(', ') : _('No device')
			}];
		},

		onSave: function() {
			// event stub
		}
	});
});
