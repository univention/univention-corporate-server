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
	"dojo/on",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dijit/Dialog",
	"umc/tools",
	"umc/dialog",
	"umc/store",
	"umc/widgets/Page",
	"umc/widgets/StandbyMixin",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/widgets/MultiInput",
	"umc/widgets/Form",
	"umc/modules/setup/InterfaceWizard",
	"umc/modules/setup/InterfaceGrid",
	"umc/modules/setup/types",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, on, Memory, Observable, Dialog, tools, dialog, store, Page, StandbyMixin, TextBox, ComboBox, MultiInput, Form, InterfaceWizard, InterfaceGrid, types, _) {
	return declare("umc.modules.setup.NetworkPage", [ Page, StandbyMixin ], {
		// summary:
		//		This class renderes a detail page containing subtabs and form elements
		//		in order to edit network interfaces.

		// system-setup-boot
		wizard_mode: false,

		// __systemsetup__ user is logged in at local firefox session
		local_mode: false,

		umcpCommand: tools.umcpCommand,
		moduleStore: null,

		// internal reference to the formular containing all form widgets of an UDM object
		_form: null,

		// dicts of the original IPv4/v6 values
		_orgValues: null,

		_currentRole: null,

		physical_interfaces: [],

		postMixInProperties: function() {
			this.title = _('Network');
			this.headerText = _('Network settings');
			this.helpText = _('In the <i>network settings</i>, IP addresses (IPv4 and IPv6) as well as name servers, gateways, and HTTP proxies may be specified.');

			this.moduleStore = new Observable(new Memory({idProperty: 'interface'}));

			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: InterfaceGrid,
				name: 'interfaces',
				label: '',
				moduleStore: this.moduleStore
			}, {
				type: ComboBox,
				name: 'interfaces/primary',
				label: _('primary network interface'),
				depends: ['interfaces', 'gateway'],
				dynamicValues: lang.hitch(this, function() {
					// FIXME: howto trigger dynamicValues update
					// The primary interface can be of any type
					return array.map(this._form._widgets.interfaces.get('value'), function(item) {
						return {id: item['interface'], label: item['interface']};
					});
				})
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
				label: _('IP network devices'),
				layout: ['interfaces']
			}, {
				label: _('Global network settings'),
				layout: [ ['gateway', 'ipv6/gateway'], 'interfaces/primary', 'nameserver', 'dns/forwarder', 'proxy/http']
			}];

			this._form = new Form({
				widgets: widgets,
				layout: layout,
				scrollable: true
			});
			this._form.on('submit', lang.hitch(this, 'onSave'));

			// only show notes in an joined system in productive mode
			if (!this.wizard_mode) {
				// show a note if interfaces changes
				this.own(on.once(this._form._widgets.interfaces, 'changed', lang.hitch(this, function() {
					// TODO: only show it when IP changes??
					this.addNote(_('Changing IP address configurations may result in restarting or stopping services. This can have severe side-effects when the system is in productive use at the moment.'));
				})));
			}

			// update interfaces/primary when there are changes on the interfaces
			this._form._widgets.interfaces.on('changed', lang.hitch(this, function() {
				this._form._widgets['interfaces/primary']._loadValues();
			}));

			// reload interfaces/primary when interfaces is ready
			this._form._widgets.interfaces.ready().then(lang.hitch(this, function() {
				this._form._widgets['interfaces/primary']._loadValues();
			}));

			this.addChild(this._form);

			// FIXME: this is a hack to fix grid width to 100%, is does not work perfect
			this.on('show', lang.hitch(this, function() {
				this._form._widgets.interfaces.resize();
			}));
		},

		postCreate: function() {
			this.inherited(arguments);
			// The grid contains changes if a DHCP request was made
			this._form._widgets.interfaces.watch('gateway', lang.hitch(this, function(name, old, value) {
				// set gateway from dhcp request
				this._form._widgets.gateway.set('value', value);
			}));
			this._form._widgets.interfaces.watch('nameserver', lang.hitch(this, function(name, old, value) {
				// read nameserver or dns/forwarder
				var nameserverWidget;
				if (this._form.getWidget('nameserver').get('visible')) {
					nameserverWidget = this._form.getWidget('nameserver');
				} else {
					// if nameserver is not visible, set dns/forwarder
					nameserverWidget = this._form.getWidget('dns/forwarder');
				}
				// set nameserver from dhcp request
				nameserverWidget.set('value', value);
			}));
		},

		// TODO: reimplement
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

			// set all available interfaces
			this.physical_interfaces = _vals.interfaces;

			// copy values that do not change in their name
			var vals = {};
			array.forEach(['gateway', 'ipv6/gateway', 'proxy/http', 'interfaces/primary'], function(ikey) {
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
//			sortedIpv6.sort(this.sortInterfaces);

			// translate to our datastructure
			var interfaces = {};
			vals.ip4dynamic = false;
			array.forEach(sortedIpv4, function(idev) {
				interfaces[idev.device] = interfaces[idev.device] || { 'interface': idev.device, interfaceType: types.getTypeByDevice(idev.device) };
				if (!idev.virtual) {
					interfaces[idev.device].ip4dynamic = (idev.type == 'dynamic' || idev.type == 'dhcp');
				}
				interfaces[idev.device].ip4 = interfaces[idev.device].ip4 || [];
				interfaces[idev.device].ip4.push([
					idev.address || '',
					idev.netmask || ''
				]);
				interfaces[idev.device].ip6 = [];
			});

			// translate to our datastructure
			array.forEach(sortedIpv6, function(idev) {
				interfaces[idev.device] = interfaces[idev.device] || {};
				interfaces[idev.device].ip6 = interfaces[idev.device].ip6 || [];
				interfaces[idev.device].ip6.push([
					idev.address || '',
					idev.prefix || '',
					idev.id || ''
				]);
			});

			// dynamic ipv6 interfaces
			r = /interfaces\/([^\/]+)\/ipv6\/acceptRA/;
			array.forEach(sortedKeys, function(ikey) {
				var match = ikey.match(r);
				if (match) {
					interfaces[match[1]].ip6dynamic = tools.isTrue(_vals[ikey]);
				}
			});

			tools.forIn(interfaces, function(device) {
				// hack it! the formatter does not know about itself
				interfaces[device].information = interfaces[device];
			});

			vals.interfaces = interfaces;
			// set all physical interfaces for the grid here, the info does not exists on grid creation
			this._form._widgets.interfaces.set('physical_interfaces', this.physical_interfaces);

			// only show forwarder for master, backup, and slave
			this._currentRole = _vals['server/role'];
			var showForwarder = this._currentRole == 'domaincontroller_master' || this._currentRole == 'domaincontroller_backup' || this._currentRole == 'domaincontroller_slave';
			this._form.getWidget('dns/forwarder').set('visible', showForwarder);

			// hide domain nameserver on master when using system setup boot
			this._form.getWidget('nameserver').set('visible', ! ( this.wizard_mode && this._currentRole == 'domaincontroller_master' ) );
			// set values
			this._form.setFormValues(vals);

			this.clearNotes();
		},

		getValues: function() {
			var _vals = this._form.get('value');
			var vals = {};

			// copy values that do not change in their name
			array.forEach(['gateway', 'ipv6/gateway', 'proxy/http', 'interfaces/primary'], function(ikey) {
				vals[ikey] = _vals[ikey];
			});

			// copy lists of nameservers/forwarders
			array.forEach(['nameserver', 'dns/forwarder'], function(iname) {
				array.forEach(_vals[iname], function(jval, j) {
					vals[iname + (j + 1)] = jval;
				});
			});

			array.forEach(_vals.interfaces, function(iface) {
				var iname = iface['interface'];
				if (iface.interfaceType === 'eth' || iface.interfaceType === 'vlan') {
					if (iface.ip4.length) {
						// IPv4
						array.forEach(iface.ip4, function(virtval, i) {
							var iaddress = virtval[0];
							var imask = virtval[1];
							if (i === 0) {
								// IP address
								vals['interfaces/' + iname + '/address'] = iaddress;
								vals['interfaces/' + iname + '/netmask'] = imask;
							} else {
								// virtual ip adresses
								vals['interfaces/' + iname + '_' + (i-1) + '/address'] = iaddress;
								vals['interfaces/' + iname + '_' + (i-1) + '/netmask'] = imask;
							}
						});
					} else if (iface.ip4dynamic) {
						// DHCP
						vals['interfaces/' + iname + '/type'] = 'dynamic';
					}

					// IPv6 SLAAC
					vals['interfaces/' + iname + '/ipv6/acceptRA'] = iface.ip6dynamic ? 'true' : 'false';

					if (!iface.ip6dynamic) {
						// IPv6
						array.forEach(iface.ip6, function(ip6val) {
							var iaddress = ip6val[0];
							var iprefix = ip6val[1];
							var iidentifier = ip6val[2];
							vals['interfaces/' + iname + '/ipv6/' + iidentifier + '/address'] = iaddress;
							vals['interfaces/' + iname + '/ipv6/' + iidentifier + '/prefix'] = iprefix;
						});
					}
				}
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

			allInterfaces = array.map(this._form._widgets.interfaces.get('value'), function(item) {
				return item['interface'];
			});

			// list of all IPv4 network devices
			var vals = this._form.get('value');
			var ipv4Str = array.map(array.filter(vals.interfaces, function(idev) {
				return idev.ip4.length;
			}), function(idev) {
				if (idev.ip4dynamic) {
					return idev['interface'] + ': DHCP';
				}
				return idev['interface'] + ': ' + array.map(idev.ip4, function(ip4) {
					// address/netmask
					return ip4[0] + '/' + ip4[1];
				}).join(', ');
			});

			ipv4Str = ipv4Str.length ? '<ul><li>' + ipv4Str.join('</li><li>') + '</li></ul>' : '';

			var ipv6Str = array.map(array.filter(vals.interfaces, function(idev) {
				return idev.ip6 && idev.ip6.length;
			}), function(idev) {
				if (idev.ip6dynamic) {
					return idev['interface'] + ': DHCP';
				}
				return idev['interface'] + ': ' + array.map(idev.ip6, function(ip6) {
					// adress - prefix/identifier
					return ip6[0] + ' - ' + ip6[1] + '/' + ip6[2];
				}).join(', '); // TODO: <br> or <li>
			});

			ipv6Str = ipv6Str.length ? '<ul><li>' + ipv6Str.join('</li><li>') + '</li></ul>' : '';

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
				variables: ['interfaces/primary'],
				description: _('primary network interface'),
				values: vals['interfaces/primary']
//			}, {
				// FIXME
//				variables: [/^interfaces\/[^\/]+\/ipv6\/acceptRA/],
//				description: _('IPv6 interfaces with autoconfiguration (SLAAC)'),
//				values: vals['dynamic_interfaces_ipv6'].length ? vals['dynamic_interfaces_ipv6'].join(', ') : _('No device')
			}];
		},

		onSave: function() {
			// event stub
		}
	});
});
