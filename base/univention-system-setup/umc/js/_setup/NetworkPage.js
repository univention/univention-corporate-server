/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._setup.NetworkPage");

dojo.require("dojo.DeferredList");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TabContainer");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.modules._setup.NetworkPage", [ umc.widgets.Page, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	// summary:
	//		This class renderes a detail page containing subtabs and form elements
	//		in order to edit UDM objects.

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.setup',

	umcpCommand: umc.tools.umcpCommand,

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	// dicts of the original IPv4/v6 values
	_orgValues: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		this.title = this._('Network');
		this.headerText = this._('Network settings');
	},

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'MultiInput',
			name: 'interfaces_ipv4',
			label: '', //this._('Interfaces'),
			umcpCommand: this.umcpCommand,
			subtypes: [{
				type: 'ComboBox',
				label: this._('Interface'),
				dynamicValues: dojo.hitch(this, function() {
					return this.umcpCommand('setup/net/interfaces').then(dojo.hitch(this, function(data) {
						// for ipv4 interfaces, we can have a virtual one, as well
						var list = [];
						dojo.forEach(data.result, function(idev) {
							var idev2 = {
								id: idev + '_virtual',
								label: idev + ' (' + this._('virtual') + ')'
							};
							list.push(idev, idev2);
						}, this);
						return list;
					}));
				}),
				style: 'width: 7em'
			}, {
				type: 'TextBox',
				label: this._('IPv4 address'),
				style: 'width: 14em'
			}, {
				type: 'TextBox',
				label: this._('Netmask'),
				style: 'width: 14em'
			}, {
				type: 'ComboBox',
				label: this._('Dynamic (DHCP)'),
				staticValues: [
					{ id: 'false', label: this._('Deactivated') },
					{ id: 'true', label: this._('Activated') }
				],
				style: 'width: 10em'
			}, {
				type: 'Button',
				label: 'DHCP query',
				callback: dojo.hitch(this, '_dhcpQuery')
			}]
		}, {
			type: 'MultiInput',
			name: 'interfaces_ipv6',
			label: this._('Interfaces'),
			umcpCommand: this.umcpCommand,
			subtypes: [{
				type: 'ComboBox',
				label: this._('Interface'),
				dynamicValues: 'setup/net/interfaces',
				style: 'width: 7em'
			}, {
				type: 'TextBox',
				label: this._('Identifier'),
				style: 'width: 7em'
			}, {
				type: 'TextBox',
				label: this._('IPv6 address'),
				style: 'width: 20em'
			}, {
				type: 'TextBox',
				label: this._('IPv6 prefix'),
				style: 'width: 12em'
			}]
		}, {
			type: 'MultiSelect',
			name: 'dynamic_interfaces_ipv6',
			label: this._('Autoconfiguration (SLAAC)'),
			umcpCommand: this.umcpCommand,
			dynamicValues: 'setup/net/interfaces',
			autoHeight: true
		}, {
			type: 'TextBox',
			name: 'gateway',
			label: this._('Gateway (IPv4)')
		}, {
			type: 'TextBox',
			name: 'ipv6/gateway',
			label: this._('Gateway (IPv6)')
		}, {
			type: 'MultiInput',
			subtypes: [{ type: 'TextBox' }],
			name: 'nameserver',
			label: this._('Domain name server (max. 3)'),
			max: 3
		}, {
			type: 'MultiInput',
			subtypes: [{ type: 'TextBox' }],
			name: 'dns/forwarder',
			label: this._('External name server (max. 3)'),
			max: 3
		}, {
			type: 'TextBox',
			name: 'proxy/http',
			label: this._('HTTP proxy')
		}];

		var layout = [{
			label: this._('IPv4 network devices'),
			layout: ['interfaces_ipv4']
		}, {
			label: this._('IPv6 network devices'),
			layout: ['interfaces_ipv6', 'dynamic_interfaces_ipv6']
		}, {
			label: this._('Global network settings'),
			layout: [ ['gateway', 'ipv6/gateway'], 'nameserver', 'dns/forwarder', 'proxy/http']
		}];

		this._form = new umc.widgets.Form({
			widgets: widgets,
			layout: layout,
			onSubmit: dojo.hitch(this, 'onSave'),
			scrollable: true
		});

		this.addChild(this._form);
	},

	_dhcpQuery: function(item, idx) {
		// switch on standby animation
		this.standby(true);

		// make sure we have an interface selected
		if (!item || !item[0] || !dojo.isString(item[0])) {
			umc.dialog.alert(this._('Please choose a network device before querying a DHCP address.'));
			this.standby(false);
			return;
		}
		if (item[0].indexOf('_virtual') >= 0) {
			umc.dialog.alert(this._('A virtual network device cannot be used for DHCP.'));
			this.standby(false);
			return;
		}
		this.umcpCommand('setup/net/dhclient', {
			'interface': item[0]
		}).then(dojo.hitch(this, function(data) {
			// switch off standby animation
			this.standby(false);

			var result = data.result;
			if (!result.address && !result.netmask) {
				umc.dialog.alert(this._('DHCP query failed.'));
				return;
			}

			// set the queried IP and netmask
			var devicesWidget = this._forms.network.getWidget('interfaces_ipv4');
			var val = devicesWidget.get('value');
			if (result.address) {
				val[idx][1] = result.address;
			}
			if (result.netmask) {
				val[idx][2] = result.netmask;
			}
			val[idx][3] = 'false';
			devicesWidget.set('value', val);
		}), dojo.hitch(this, function() {
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
		var r = /^(interfaces\/(eth[0-9]+).*|nameserver[1-3]|dns\/forwarder[1-3])$/;
		this._orgValues = {};
		umc.tools.forIn(_vals, function(ikey, ival) {
			if (r.test(ikey)) {
				this._orgValues[ikey] = ival;
			}
		}, this);

		// copy values that do not change in their name
		var vals = {};
		dojo.forEach(['gateway', 'ipv6/gateway', 'proxy/http'], function(ikey) {
			vals[ikey] = _vals[ikey];
		});

		// sort the keys such that the interface order is correct
		var sortedKeys = [];
		umc.tools.forIn(_vals, function(ikey) {
			sortedKeys.push(ikey);
		});
		sortedKeys.sort();

		// copy lists of nameservers/forwarders
		vals.nameserver = [];
		vals['dns/forwarder'] = [];
		dojo.forEach(sortedKeys, function(ikey) {
			dojo.forEach(['nameserver', 'dns/forwarder'], function(jname) {
				if (0 === ikey.indexOf(jname)) {
					vals[jname].push(_vals[ikey]);
				}
			});
		});

		// copy ipv4 interfaces
		r = /interfaces\/((eth[0-9]+)(_([0-9]))?)\/(.+)/;
		var ipv4 = {};
		dojo.forEach(sortedKeys, function(ikey) {
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
		umc.tools.forIn(ipv4, function(ikey, ival) {
			sortedIpv4.push(ival);
		});

		// translate to our datastructure
		vals.interfaces_ipv4 = [];
		dojo.forEach(sortedIpv4, function(idev) {
			vals.interfaces_ipv4.push([
				idev.virtual ? idev.device + '_virtual' : idev.device,
				idev.address || '',
				idev.netmask || '',
				idev.type == 'dynamic' || idev.type == 'dhcp' ? 'true' : 'false'
			]);
		});

		// copy ipv6 interfaces
		r = /interfaces\/(eth[0-9]+)\/ipv6\/([^\/]+)\/(.+)/;
		var ipv6 = {};
		dojo.forEach(sortedKeys, function(ikey) {
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
		umc.tools.forIn(ipv6, function(ikey, ival) {
			sortedIpv6.push(ival);
		});
		sortedIpv6.sort(this.sortInterfaces);

		// translate to our datastructure
		vals.interfaces_ipv6 = [];
		dojo.forEach(sortedIpv6, function(idev) {
			vals.interfaces_ipv6.push([
				idev.device,
				idev.id || '',
				idev.address || '',
				idev.prefix || ''
			]);
		});

		// dynamic ipv6 interfaces
		r = /interfaces\/(eth[0-9]+)\/ipv6\/acceptRA/;
		vals.dynamic_interfaces_ipv6 = [];
		dojo.forEach(sortedKeys, function(ikey) {
			var match = ikey.match(r);
			if (umc.tools.isTrue(_vals[ikey]) && match) {
				vals.dynamic_interfaces_ipv6.push(match[1]);
			}
		});

		this._form.setFormValues(vals);
	},

	getValues: function() {
		var _vals = this._form.gatherFormValues();
		var vals = {};

		// copy values that do not change in their name
		dojo.forEach(['gateway', 'ipv6/gateway', 'proxy/http'], function(ikey) {
			vals[ikey] = _vals[ikey];
		});

		// copy lists of nameservers/forwarders
		dojo.forEach(['nameserver', 'dns/forwarder'], function(iname) {
			dojo.forEach(_vals[iname], function(jval, j) {
				vals[iname + (j + 1)] = jval;
			});
		});

		// copy ipv4 interfaces
		var iipv4Virtual = {};  // counter for the virtual interfaces
		dojo.forEach(_vals.interfaces_ipv4, function(ival) {
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
		dojo.forEach(_vals.interfaces_ipv6, function(ival) {
			var idev = ival[0];
			var iid = ival[1];
			var iaddress = ival[2];
			var iprefix = ival[3];
			vals['interfaces/' + idev + '/ipv6/' + iid + '/address'] = iaddress;
			vals['interfaces/' + idev + '/ipv6/' + iid + '/prefix'] = iprefix;
		});

		// dynamic ipv6 interfaces
		//dojo.forEach(_vals.dynamic_interfaces_ipv6, function(idev) {
		dojo.forEach(this._form.getWidget('dynamic_interfaces_ipv6').getAllItems(), function(iitem) {
			vals['interfaces/' + iitem.id + '/ipv6/acceptRA'] = (dojo.indexOf(_vals.dynamic_interfaces_ipv6, iitem.id) >= 0) ? 'true' : 'false';
		});

		// add empty entries for all original entries that are not used anymore
		umc.tools.forIn(this._orgValues, function(ikey, ival) {
			if (!(ikey in vals)) {
				vals[ikey] = '';
			}
		});

		return vals;
	},

	getSummary: function() {
		// a list of all components with their labels
		var allInterfaces = {};
		dojo.forEach(this._form.getWidget('dynamic_interfaces_ipv6').getAllItems(), function(iitem) {
			allInterfaces[iitem.id] = iitem.label;
			allInterfaces[iitem.id + '_virtual'] = iitem.label + ' [' + this._('virtual') + ']';
		}, this);

		// list of all IPv4 network devices
		var vals = this._form.gatherFormValues();
		var ipv4Str = '<ul>';
		dojo.forEach(vals.interfaces_ipv4, function(idev) {
			ipv4Str += '<li>' +
					idev[1] + '/' + idev[2] +
					' (' +
						allInterfaces[idev[0]] +
						(idev[3] == 'true' ? ', DHCP' : '') +
					')</li>';
		});
		ipv4Str += '</ul>';

		// list of all IPv6 network devices
		var ipv6Str = '<ul>';
		dojo.forEach(vals.interfaces_ipv6, function(idev) {
			ipv6Str += '<li>' +
					idev[1] + ' - ' + idev[2] + '/' + idev[3] +
					' (' + idev[0] + ')</li>';
		});
		ipv6Str += '</ul>';

		// create a verbose list of all settings
		return [{
			variables: ['gateway'],
			description: this._('Gateway (IPv4)'),
			values: vals['gateway']
		}, {
			variables: ['ipv6/gateway'],
			description: this._('Gateway (IPv6)'),
			values: vals['ipv6/gateway']
		}, {
			variables: [/nameserver.*/],
			description: this._('Domain name server'),
			values: vals['nameserver'].join(', ')
		}, {
			variables: [/dns\/forwarder.*/],
			description: this._('External name server'),
			values: vals['dns/forwarder'].join(', ')
		}, {
			variables: ['proxy/http'],
			description: this._('HTTP proxy'),
			values: vals['proxy/http']
		}, {
			variables: [/^interfaces\/eth[0-9]+(_[0-9])?\/(?!ipv6).*/],
			description: this._('IPv4 network devices'),
			values: ipv4Str
		}, {
			variables: [/^interfaces\/eth[0-9]+\/ipv6\/.*\/(prefix|address)$/],
			description: this._('IPv6 network devices'),
			values: ipv6Str
		}, {
			variables: [/^interfaces\/eth[0-9]+\/ipv6\/acceptRA/],
			description: this._('IPv6 interfaces with autoconfiguration (SLAAC)'),
			values: vals['dynamic_interfaces_ipv6'].length ? vals['dynamic_interfaces_ipv6'].join(', ') : this._('No device')
		}];
	},

	onSave: function() {
		// event stub
	}
});



