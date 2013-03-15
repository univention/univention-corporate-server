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
/*global define console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/aspect",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/StandbyMixin",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/widgets/MultiInput",
	"umc/widgets/Form",
	"umc/modules/setup/InterfaceGrid",
	"umc/i18n!umc/modules/setup",
	"umc/modules/setup/types",
	"umc/modules/setup/InterfaceWizard"
], function(declare, lang, array, aspect, tools, Page, StandbyMixin, TextBox, ComboBox, MultiInput, Form, InterfaceGrid, _) {
	return declare("umc.modules.setup.NetworkPage", [ Page, StandbyMixin ], {
		// summary:
		//		This class renderes a detail page containing subtabs and form elements
		//		in order to edit network interfaces.

		// system-setup-boot
		wizard_mode: false,

		// __systemsetup__ user is logged in at local firefox session
		local_mode: false,

		umcpCommand: tools.umcpCommand,

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

			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: InterfaceGrid,
				name: 'interfaces',
				label: ''
			}, {
				type: ComboBox,
				name: 'interfaces/primary',
				label: _('primary network interface')
//				depends: ['interfaces', 'gateway']
//				dynamicValues: lang.hitch(this, function(values) {
//					// The primary interface can be of any type
//					return array.map(values.interfaces, function(iface) {
//						return {id: iface['interface'], label: iface['interface']};
//					});
//				})
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
				layout: [ ['gateway', 'ipv6/gateway'], 'nameserver', 'dns/forwarder', 'proxy/http']
			}];

			this._form = new Form({
				widgets: widgets,
				layout: layout,
				scrollable: true
			});
			this._form.on('submit', lang.hitch(this, 'onSave'));

			this.addChild(this._form);

			// FIXME: as the grid is a border container it has to be resized manually if it is used as form element
			this.own(aspect.after(this, 'resize', lang.hitch(this, function() {
					this._form._widgets.interfaces.resize();
			})));
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
			this._form._widgets.interfaces.watch('interfaces/primary', lang.hitch(this, function(name, old, value) {
				// set new primary interface
				this._form._widgets['interfaces/primary'].set('value', value);
			}));
		},

		setValues: function(_vals) {

			// save a copy of all original values that may be lists
			var r = /^(interfaces\/.*|nameserver[1-3]|dns\/forwarder[1-3])$/;
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

			var interfaces = {};
			// create the scheme
			r = /interfaces\/(([^_\/]+)[0-9.]+)\//; // TODO: enhance?
			tools.forIn(_vals, function(ikey) {
				var match = ikey.match(r);
				if (match) {
					var name = match[1];
					var vlan_id = null;

					if (interfaces[name]) {
						return; // already parsed
					}

					var interfaceType = 'eth';
					// vlan device?
					if(/[.]/.test(match[2])) {
						vlan_id = parseInt(match[2].match(/[^.]+[.]([0-9]+)/)[1], 10);
						interfaceType = 'vlan';
					}

					var primary = _vals['interfaces/primary'] === name;

					interfaces[name] = {
						// every device
						'interface': name,
						interfaceType: interfaceType, // eth|vlan|bond|br
						ip4: [['', '']],
						ip6: [['', '', '']],
						ip4dynamic: null,
						ip6dynamic: null,
						start: null, // true|false
//						type: null, // static|dhcp|manual
						primary: primary,

						// for vlan devices
						vlan_id: vlan_id,

						// for bonding devices
						'bond-mode': null,
						'bond-slaves': [],
						'bond-primary': [],
						miimon: null,

						// for bridge devices
						bridge_ports: [],
						bridge_fd: 0
					};
				}
			});

			var stored = {};
			// parse (also virtual) interfaces
			r = /interfaces\/(([^_\/]+)(_([0-9]+))?)\/(.+)/;
			tools.forIn(_vals, function(ikey, typeval) {
				var match = ikey.match(r);
				if (match) {
					var iorig = match[1]; // the whole interface string
					var iname = match[2]; // the device name
					var ivirtual = parseInt(match[4], 10); // the virtual id number or NaN
					var virtual = !isNaN(ivirtual);
					var type = match[5]; // the rest of the string

					var temp = stored[iname] || {};
					temp.data = temp.data || {};
					temp.virtual = temp.virtual || {};
					temp.ip6 = temp.ip6 || {};
					temp.options = temp.options || {};

					if (virtual) {
						// TODO: check if there are other values which can be set on an virtual interface
						if (type == 'address' || type == 'netmask') {
							temp.virtual[ivirtual] = temp.virtual[ivirtual] || {};
							temp.virtual[ivirtual][type] = typeval;
						} else {
							console.warn('FIXME: got unexpected variable: ' + type + '=' + typeval);
						}
					} else {
						var ip6match = type.match(/ipv6\/([^\/]+)\/(.+)/);
						var roptions = type.match(/options\/([0-9]+)$/);
						if (array.indexOf(['address', 'netmask', 'type', 'start', 'ipv6/acceptRA'], type) !== -1) {
							temp.data[type] = typeval;
						} else if (ip6match) {
							var identifier = ip6match[1];
							var type6 = ip6match[2];
							temp.ip6[identifier] = temp.ip6[identifier] || {};
							if (type6 == 'address' || type6 == 'prefix') {
								temp.ip6[identifier][type6] = typeval;
							} else {
								console.warn('FIXME: got unexpected variable: ' + type + '=' + typeval);
							}
						} else if (roptions) {
							var num = roptions[1];
							var not_matched = true;

							// parse interface options
							tools.forIn({
								miimon: function(val) { return parseInt(val, 10); },
								'bond-mode': function(val) { return parseInt(val, 10); },
								'bond-slaves': function(val) { return val.split(' '); },
								'bond-primary': function(val) { return val.split(' '); },
								bridge_ports: function(val) { return val.split(' '); },
								bridge_fd: function(val) { return parseInt(val, 10); }
							}, function(opt, formatter) {
								var r = new RegExp('^' + opt + '\\s*(.*)\\s*$');
								match = typeval.match(r);
								if (match) {
									temp.options[opt] = formatter(match[1]);
									not_matched = false;
									return false; // break loop
								}
							});

							if (not_matched) {
								// TODO: store it and set it back

							}
						} else {
							if (-1 === array.indexOf(['broadcast', 'network', 'order', 'mac', 'host'], type) && type.indexOf('route/') !== 0) {
								console.warn('FIXME: got unexpected variable: ' + type + '=' + typeval);
							}
						}
					}

					stored[iname] = temp;
				}
			});

			tools.forIn(stored, function(iname, ivalue, iobj) {

				// set interfaceType
				if (interfaces[iname].interfaceType !== 'vlan') {
					if (ivalue.options['bond-primary']) {
						interfaces[iname].interfaceType = 'bond';
					} else if (ivalue.options['bridge_ports']) {
						interfaces[iname].interfaceType = 'br';
					}
				}

				// DHCP
				if (ivalue.data.type == 'dhcp') {
					interfaces[iname].ip4dynamic = true;
				} else {
					// set primary IP address
					interfaces[iname].ip4[0][0] = ivalue.data.address || "";
					interfaces[iname].ip4[0][1] = ivalue.data.netmask || '255.255.255.0';
				}

				// set virtual IP addresses
				tools.forIn(ivalue.virtual, function(inum, ivirt) {
					interfaces[iname].ip4.push([ivirt.address || "", ivirt.netmask || ""]);
				});

				// SLAAC
				if (undefined !== ivalue.data['ipv6/acceptRA']) {
					interfaces[iname].ip6dynamic = tools.isTrue(ivalue.data['ipv6/acceptRA']);
				}

				// set primary IP6 address
				if (ivalue.ip6['default']) {
					interfaces[iname].ip6[0] = [ivalue.ip6['default'].address || "", ivalue.ip6['default'].prefix || "", 'default'];
				}

				// set virtual IP6 addresses
				tools.forIn(ivalue.ip6, function(id, ival) {
					if (id === 'default') {
						return; // already entered
					}
					interfaces[iname].ip6.push([ival.address || "", ival.prefix || "", id]);
				});

				// set options
				tools.forIn(ivalue.options, function(ikey, ival) {
					 interfaces[iname][ikey] = ival;
				});
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

			// show a note if interfaces changes
			if (!this.wizard_mode) {
				// only show notes in an joined system in productive mode
				var handler = this._form._widgets.interfaces.watch('value', lang.hitch(this, function() {
					// TODO: only show it when IP changes??
					this.addNote(_('Changing IP address configurations may result in restarting or stopping services. This can have severe side-effects when the system is in productive use at the moment.'));
					handler.unwatch();
				}));
				this.own(handler);
			}
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

			array.forEach(_vals.interfaces, lang.hitch(this, function(iface) {
				var iname = iface['interface'];

				iface.type !== undefined && iface.type !== null && (vals['interfaces/' + iname + '/type'] = iface.type);
				iface.start !== undefined && iface.start !== null && (vals['interfaces/' + iname + '/start'] = iface.start);

				if (array.some(_vals.interfaces, function(iiface) {
					var ikey = iiface.interfaceType === 'bond' ? 'bond-slaves' : 'bridge_ports';
					return (iiface.interfaceType === 'bond' || iiface.interfaceType === 'br') && -1 !== array.indexOf(iiface[ikey], iname);
				})) {
					// The device is used in a bridge or bonding, so remove its IPs
					vals['interfaces/' + iname + '/address'] = '';
					vals['interfaces/' + iname + '/netmask'] = '';

					// assert iface.interfaceType === 'eth' || iface.interfaceType === 'vlan') && iface.type === 'manual'

				} else {
					// the device is not used by a bridge or bonding, so we configure its IP addresses

					if (iface.interfaceType === 'br' || iface.interfaceType === 'bond') {
						// for bonding and bridging this must/should be set
						// for eth and vlan we don't want to overwrite existing settings
						vals['interfaces/' + iname + '/start'] = iface.start;
						if (iface.interfaceType === 'br') {
							// FIXME: this could overwrite additional existing options
							var bp = iface.bridge_ports.length ? iface.bridge_ports.join(' ') : 'none';
							vals['interfaces/' + iname + '/options/0'] = 'bridge_ports ' + bp;
							vals['interfaces/' + iname + '/options/1'] = 'bridge_fd ' + iface.bridge_fd;
						} else if(iface.interfaceType === 'bond') {
							vals['interfaces/' + iname + '/options/0'] = 'bond-slaves ' + iface['bond-slaves'].join(' ');
							vals['interfaces/' + iname + '/options/1'] = 'bond-primary ' + iface['bond-primary'].join(' ');
							vals['interfaces/' + iname + '/options/2'] = 'bond-mode ' + iface['bond-mode'];
							vals['interfaces/' + iname + '/options/3'] = 'miimon ' + iface.miimon;
						}
					}

					if (iface.ip4dynamic) {
						// DHCP
						vals['interfaces/' + iname + '/type'] = 'dhcp';
					} else if (iface.ip4.length) {
						// IPv4
						array.forEach(iface.ip4, function(virtval, i) {
							var iaddress = virtval[0];
							var imask = virtval[1];
							if (i === 0) {
								// primary IP address
								vals['interfaces/' + iname + '/address'] = iaddress;
								vals['interfaces/' + iname + '/netmask'] = imask;
							} else {
								// virtual ip adresses
								vals['interfaces/' + iname + '_' + i + '/address'] = iaddress;
								vals['interfaces/' + iname + '_' + i + '/netmask'] = imask;
							}
						});
					}

					// IPv6 SLAAC
					vals['interfaces/' + iname + '/ipv6/acceptRA'] = iface.ip6dynamic ? 'true' : 'false';

					if (!iface.ip6dynamic) {
						// IPv6
						array.forEach(iface.ip6, function(ip6val) {
							var iaddress = ip6val[0];
							var iprefix = ip6val[1];
							var iidentifier = ip6val[2];
							if (!iidentifier) {
								return;
							}
							vals['interfaces/' + iname + '/ipv6/' + iidentifier + '/address'] = iaddress;
							vals['interfaces/' + iname + '/ipv6/' + iidentifier + '/prefix'] = iprefix;
						});
					}

					// compatibility workarounds
					array.forEach(['broadcast', 'network', 'hosts', 'mac'], lang.hitch(this, function(foobar) {
						if (this._orgValues['interfaces/' + iname + '/' + foobar]) {
							vals['interfaces/' + iname + '/' + foobar] = this._orgValues['interfaces/' + iname + '/' + foobar];
						}
					}));
				}
			}));

			var non_eth_interfaces = array.map(array.filter(this._form._widgets.interfaces.get('value'), function(item) { return item.interfaceType !== 'eth';}), function(item) {
				return item['interface'];
			});

			tools.forIn(vals, function(ikey) {
				// remove every non eth interface
				array.forEach(non_eth_interfaces, lang.hitch(this, function(iiname) {
					if ((new RegExp('^interfaces/' + iiname + '/')).test(ikey)) {
						delete vals[ikey];
					}
				}));
			});

			// add empty entries for all original entries that are not used anymore
			tools.forIn(this._orgValues, function(ikey, ival) {
				// ----------- no br, bond, vlan
				// set original values for every non eth interface
				array.forEach(non_eth_interfaces, lang.hitch(this, function(iiname) {
					if ((new RegExp('^interfaces/' + iiname + '/')).test(ikey)) {
						vals[ikey] = ival;
					}
				}));
				// ------------------------
				if (!(ikey in vals)) {
					vals[ikey] = '';
				}
			});

			vals['interfaces/primary'] = this._orgValues['interfaces/primary'];

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
					return idev['interface'] + ': ' + _('Dynamic (DHCP)');
				}
				return idev['interface'] + ': ' + array.map(array.filter(idev.ip4, function(ip4) { return ip4[0] && ip4[1]; }), function(ip4) {
					// address/netmask
					return ip4[0] + '/' + ip4[1];
				}).join(', ');
			});

			ipv4Str = ipv4Str.length ? '<ul><li>' + ipv4Str.join('</li><li>') + '</li></ul>' : '';

			var ipv6Str = array.map(array.filter(vals.interfaces, function(idev) {
				return idev.ip6 && idev.ip6.length;
			}), function(idev) {
				if (idev.ip6dynamic) {
					return idev['interface'] + ': ' + _('Autoconfiguration (SLAAC)');
				}
				return idev['interface'] + ': ' + array.map(array.filter(idev.ip6, function(ip6) { return ip6[0] && ip6[1]; }), function(ip6) {
					// identifier: address/prefix
					return ip6[2] + ': ' + ip6[0] + '/' + ip6[1];
				}).join(', '); // TODO: <br> or <li>?
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
				variables: [(/nameserver.*/)],
				description: _('Domain name server'),
				values: vals['nameserver'].join(', ')
			}, {
				variables: [(/dns\/forwarder.*/)],
				description: _('External name server'),
				values: vals['dns/forwarder'].join(', ')
			}, {
				variables: ['proxy/http'],
				description: _('HTTP proxy'),
				values: vals['proxy/http']
			}, {
				variables: [(/^interfaces\/[^_\/]+(_[0-9]+)?\/(?!ipv6).*/)],
				description: _('IPv4 network devices'),
				values: ipv4Str
			}, {
				variables: [(/^interfaces\/[^\/]+\/ipv6\/.*\/(prefix|address)$/)],
				description: _('IPv6 network devices'),
				values: ipv6Str
			}, {
				variables: ['interfaces/primary'],
				description: _('primary network interface'),
				values: vals['interfaces/primary']
			}, {
				variables: [/^interfaces\/[^\/]+\/ipv6\/acceptRA/],
				description: _('IPv6 interfaces with autoconfiguration (SLAAC)'),
				values: array.map(array.filter(vals.interfaces, function(iface) { return iface.ip6dynamic; }), function(iface) { return iface['interface']; }).join(', ') || _('No device')
			}];
		},

		onSave: function() {
			// event stub
		}
	});
});
