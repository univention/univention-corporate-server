/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.setup");

dojo.require("dijit.TitlePane");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.TabbedModule");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TitlePane");

dojo.declare("umc.modules.setup", [ umc.widgets.TabbedModule, umc.i18n.Mixin ], {

	i18nClass: 'umc.modules.setup',

	pages: [ 'LanguagePage', 'ServerPage' ],

	wizard: false,

	_pages: null,

	_orgValues: null,

	buildRendering: function() {
		this.inherited(arguments);

		this.standby(true);

		// each page has the same buttons for saving/resetting
		var buttons = [{
			name: 'submit',
			label: this._('Save'),
			callback: dojo.hitch(this, function() {
				this.save(this.getValues());
			})
		}, {
			name: 'restore',
			label: this._('Reset'),
			callback: dojo.hitch(this, function() {
				this.setValues(this._orgValues);
			})
		}];

		// create all pages dynamically
		this._pages = [];
		dojo.forEach(this.pages, function(iclass) {
			var ipath = 'umc.modules._setup.' + iclass;
			dojo['require'](ipath);
			var ipage = new dojo.getObject(ipath)({
				footerButtons: buttons,
				onSave: dojo.hitch(this, function() {
					this.save(this.getValues());
				})
			});
			this.addChild(ipage);
			this._pages.push(ipage);
		}, this);

		// get settings from server
		umc.tools.umcpCommand('setup/load').then(dojo.hitch(this, function(data) {
			// update setup pages with loaded values
			this.setValues(data.result);
			this.standby(false);
		}), dojo.hitch(this, function() {
			this.standby(false);
		}));
/*
        this._makePage(
			'network',
			this._("Network"),
            this._("Network settings"),
			undefined,
			[{
				type: 'MultiInput',
				name: 'devices_ipv4',
				label: this._('Devices'),
				subtypes: [{
					type: 'ComboBox',
					label: this._('Device'),
					dynamicValues: 'setup/net/interfaces',
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
					callback: dojo.hitch(this, function(item, idx) {
						// switch on standby animation
						this.standby(true);

						// make sure we have an interface selected
						if (!item || !item[0] || !dojo.isString(item[0])) {
							umc.dialog.alert(this._('Please choose a network device before querying a DHCP address.'));
							this.standby(false);
							return;
						}
						umc.tools.umcpCommand('setup/net/dhclient', {
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
							var devicesWidget = this._forms.network.getWidget('devices_ipv4');
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
					})
				}]
			}, {
				type: 'MultiInput',
				name: 'devices_ipv6',
				label: this._('Devices'),
				subtypes: [{
					type: 'ComboBox',
					label: this._('Device'),
					staticValues: [ 'eth0', 'eth1', 'eth2' ],
					style: 'width: 7em'
				}, {
					type: 'TextBox',
					label: this._('IPv6 address')
				}, {
					type: 'TextBox',
					label: this._('IPv6 prefix'),
					style: 'width: 14em'
				}, {
					type: 'ComboBox',
					label: this._('Dynamic'),
					staticValues: [
						{ id: 'false', label: this._('Deactivated') },
						{ id: 'true', label: this._('Activated') }
					],
					style: 'width: 10em'
				}]
			}, {
				type: 'TextBox',
				name: 'gateway_ipv4',
				label: this._('Gateway')
			}, {
				type: 'TextBox',
				name: 'gateway_ipv6',
				label: this._('Gateway')
			}, {
				type: 'MultiInput',
				subtypes: [{ type: 'TextBox' }],
				name: 'nameServer',
				label: this._('Domain name server (max. 3)')
			}, {
				type: 'MultiInput',
				subtypes: [{ type: 'TextBox' }],
				name: 'forwarder',
				label: this._('External name server (max. 3)')
			}, {
				type: 'TextBox',
				name: 'proxy',
				label: this._('HTTP proxy')
			}],
			[{
				label: this._('IPv4 network device settings'),
				layout: ['devices_ipv4', 'gateway_ipv4']
			}, {
				label: this._('IPv6 network device settings'),
				layout: ['devices_ipv6', 'gateway_ipv6']
			}, {
				label: this._('DNS settings'),
				layout: ['nameServer', 'forwarder', 'proxy']
			}]
		);

        this._makePage(
			'security',
			this._("Security"),
            this._("Security settings"),
			undefined,
			[{
				type: 'Text',
				name: 'text',
				content: this._('<p>These options control which system services are initially blocked via packet filtering (iptables).<br>The locked-down setup only allows SSH, LDAP, HTTPS, UCS UMC and UDM Listeners/Modifiers.</p>')
			}, {
				type: 'ComboBox',
				name: 'security',
				label: this._('Filtering of system services'),
				staticValues: [{
					id: 'disabled',
					label: this._('Disabled')
				}, {
					id: 'typical',
					label: this._('Typical selection of services (recommended)')
				}, {
					id: 'locked',
					label: this._('Locked-down setup')
				}]
			}],
			[{
				label: this._('Security settings'),
				layout: ['text', 'security']
			}]
		);

        this._makePage(
			'certificate',
			this._("Certificate"),
            this._("Certificate settings"),
			undefined,
			[{
				type: 'TextBox',
				name: 'countryCode',
				label: this._('Contry code'),
				style: 'width: 7em'
			}, {
				type: 'TextBox',
				name: 'country',
				label: this._('Country'),
				style: 'width: 16.5em'
			}, {
				type: 'TextBox',
				name: 'location',
				label: this._('Location')
			}, {
				type: 'TextBox',
				name: 'organisation',
				label: this._('Organisation')
			}, {
				type: 'TextBox',
				name: 'unit',
				label: this._('Business unit')
			}, {
				type: 'TextBox',
				name: 'email',
				label: this._('Email address')
			}],
			[{
				label: this._('Country settings'),
				layout: [ ['countryCode', 'country'], 'location' ]
			}, {
				label: this._('Organisation settings'),
				layout: [ 'organisation', 'unit', 'email' ]
			}]
		);

		this._makePage(
			'software',
			this._("Software"),
			this._("Software settings"),
			undefined,
			[{
				type: 'CheckBox',
				name: 'desktop',
				label: this._('Desktop environment'),
				value: true
			}, {
				type: 'Text',
				name: 'text0',
				content: '&nbsp;'
			}, {
				type: 'CheckBox',
				name: 'samba4',
				label: this._('Samba 4 server'),
				value: true
			}, {
				type: 'CheckBox',
				name: 'samba3',
				label: this._('Samba 3 server'),
				value: false
			}, {
				type: 'CheckBox',
				name: 'adconnector',
				label: this._('Active Directory Connector'),
				value: false
			}, {
				type: 'Text',
				name: 'text1',
				content: '&nbsp;'
			}, {
				type: 'CheckBox',
				name: 'mail',
				label: this._('Mail sever (Postfix, Cyrus IMAPd, Horde 4)'),
				value: false
			}, {
				type: 'CheckBox',
				name: 'dhcp',
				label: this._('DHCP server'),
				value: true
			}, {
				type: 'CheckBox',
				name: 'cups',
				label: this._('Print server (CUPS)'),
				value: false
			}, {
				type: 'CheckBox',
				name: 'squid',
				label: this._('Web proxy server (Squid)'),
				value: false
			}, {
				type: 'CheckBox',
				name: 'bacula',
				label: this._('Backup (Bacula)'),
				value: false
			}, {
				type: 'Text',
				name: 'text2',
				content: '&nbsp;'
			}, {
				type: 'CheckBox',
				name: 'nagios',
				label: this._('Network monitoring (Nagios)'),
				value: true
			}, {
				type: 'CheckBox',
				name: 'softwaremonitor',
				label: this._('Software installation monitor'),
				value: undefined
			}],
			[{
				label: this._('Installation of software components'),
				layout: [ 'desktop', 'text0', 'samba4', 'samba3', 'adconnector', 'text1', 'mail', 'dhcp', 'cups', 'squid', 'bacula', 'text2', 'nagios', 'softwaremonitor' ]
			}]
		);
*/
	},

	setValues: function(values) {
		// update all pages with the given values
		this._orgValues = dojo.clone(values);
		dojo.forEach(this._pages, function(ipage) {
			ipage.setValues(this._orgValues);
		}, this);
	},

	getValues: function() {
		var values = {};
		dojo.forEach(this._pages, function(ipage) {
			dojo.mixin(values, ipage.getValues());
		}, this);
		return values;
	},

	save: function(_values) {
		// only save the true changes
		var values = {};
		var nchanges = 0;
		umc.tools.forIn(_values, function(ikey, ival) {
			if (dojo.toJson(this._orgValues[ikey]) != dojo.toJson(ival)) {
				values[ikey] = ival;
				++nchanges;
			}
		}, this);

		// only submit data to server if there are changes
		if (!nchanges) {
			umc.dialog.alert(this._('No changes have been made.'));
		}
		else {
			this.standby(true);
			umc.tools.umcpCommand('setup/save', { values: values }).then(dojo.hitch(this, function() {
				this.standby(false);
				this._orgValues = values;
			}), dojo.hitch(this, function() {
				this.standby(false);
			}));
		}
	}
});
