/*
 * Copyright 2014-2019 Univention GmbH
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
/*global define, console, require, window*/

define([
	"dojo/_base/kernel",
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/event",
	"dojo/dom-class",
	"dojo/on",
	"dojo/Evented",
	"dojo/topic",
	"dojo/Deferred",
	"dojo/promise/all",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dojo/request",
	"dijit/form/Select",
	"dijit/Tooltip",
	"dijit/focus",
	"dojox/timing/_base",
	"dojox/html/styles",
	"dojox/html/entities",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/TextBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/widgets/TitlePane",
	"umc/widgets/PasswordInputBox",
	"umc/widgets/PasswordBox",
	"umc/widgets/Wizard",
	"umc/widgets/Grid",
	"umc/widgets/RadioButton",
	"umc/widgets/ProgressBar",
	"./LiveSearch",
	"./VirtualKeyboardBox",
	"umc/i18n/tools",
	"umc/i18n!setup",
	"dojo/NodeList-manipulate"
], function(dojo, declare, lang, array, dojoEvent, domClass, on, Evented, topic, Deferred, all, Memory, Observable, request, Select, Tooltip, focusUtil, timing, styles, entities, dialog, tools, TextBox, CheckBox, ComboBox, ContainerWidget, Text, Button, TitlePane, PasswordInputBox, PasswordBox, Wizard, Grid, RadioButton, ProgressBar, LiveSearch, VirtualKeyboardBox, i18nTools, _) {

	var _Grid = declare(Grid, {
		_onRowClick: function(evt) {
			if (evt.cellIndex === 0) {
				// the checkbox cell was pressed, this does already the wanted behavior
				return true;
			}
			this._grid.selection.toggleSelect(evt.rowIndex);
			return;
		}
	});

	var _CityStore = declare('umc.modules.setup.CityStore', Evented, {
		umcpCommand: null,
		constructor: function(props) {
			lang.mixin(this, props);
		},
		lastResult: [],
		query: function(query) {
			this.emit('searching', {});
			var pattern = query.label.toString();
			if (pattern.length) {
				pattern = pattern.substring(0, pattern.length - 1);
			}
			var deferred = new Deferred();
			this.umcpCommand('setup/find_city', {
				pattern: pattern
			}, false).then(lang.hitch(this, function(response) {
				this.emit('searchFinished', {});
				if (response && response.result) {
					deferred.resolve(response.result);
					this.lastResult = response.result;
				}
				else {
					//deferred.reject();
					deferred.resolve([]);
				}
			}), lang.hitch(this, function(err) {
				this.emit('searchFinished', {});
				console.log('An error occurred:', err);
				deferred.resolve([]);
			}));
			return deferred;
		},
		get: function() {
			// dummy method, just to make sure that the class is recognized
			// as object store instance
			return {};
		}
	});

	var _regNumber = /^[0-9]+$/;
	var _regBitMask = /^1*0*$/;

	var _regEmailAddress = /^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-.]+$/;
	var _invalidEmailAddressMessage = _('Invalid e-mail address!<br/>Expected format is:<i>mail@example.com</i>');
	var _validateEmailAddress = function(email) {
		email = email || '';
		var isEmailAddress = _regEmailAddress.test(email);
		var acceptEmtpy = !email && !this.required;
		return acceptEmtpy || isEmailAddress;
	};

	var _invalidIPAddressMessage = _('Invalid IP address!<br/>Expected format is IPv4 or IPv6.');
	var _validateIPAddress = function(ip) {
		ip = ip || '';
		var acceptEmtpy = !ip && !this.required;
		return acceptEmtpy || tools.isIPv4Address(ip) || tools.isIPv6Address(ip);
	};

	var _isLinkLocalDHCPAddress = function(ip, mask) {
		return (ip.indexOf('169.254') === 0) && (mask=='255.255.0.0');
	};

	var _invalidNetmaskAndPrefixMessage = _('Invalid IPv4 net mask or IPv6 prefix!<br/>Expected for IPv4 is a number between 0 and 32 or a format similar to <i>255.255.255.0</i>.<br/>Expected format for IPv6 is a number between 0 and 128.');
	var _validateNetmaskAndPrefix = function(mask) {
		mask = mask || '';

		var acceptEmtpy = !mask && !this.required;
		if (acceptEmtpy) {
			return true;
		}

		var isNumber = _regNumber.test(mask);
		if (isNumber) {
			mask = parseInt(mask, 10);
			return mask >= 0 && mask <= 128;
		}

		if (!tools.isIPv4Address(mask)) {
			return false;
		}

		// we have something IP-like, could be a netmask, its format should be something like:
		// 11111111111111111111111100000000
		var parts = mask.split('.');
		var bits = '';
		array.forEach(parts, function(ipart) {
			var inum = parseInt(ipart, 10);
			var bit = inum.toString(2);

			// fill up missing zeros
			var zeros = '';
			for (var ibit = 8 - bit.length; ibit > 0; --ibit) {
				zeros += '0';
			}
			bits += zeros + bit;
		});
		return _regBitMask.test(bits) && bits.length == 32;
	};

	var _validateHostname = function(hostname) {
		hostname = hostname || '';
		var acceptEmtpy = !hostname && !this.required;
		return acceptEmtpy || (tools.isHostname(hostname));
	};

	var _invalidDomainNameMessage = _('Invalid domain name!<br/>Expected format: <i>mydomain.intranet</i>');
	var _validateDomainName = function(domainName) {
		domainName = domainName || '';
		var acceptEmtpy = !domainName && !this.required;
		return acceptEmtpy || (tools.isFQDN(domainName));
	};

	var _invalidFQDNMessage = _('Invalid fully qualified domain name!<br/>Expected format: <i>hostname.mydomain.intranet</i>');
	var _validateFQDN = function(fqdn) {
		fqdn = fqdn || '';
		var hasEnoughParts = fqdn.split('.').length >= 3;
		var acceptEmtpy = !fqdn && !this.required;
		return acceptEmtpy || (tools.isFQDN(fqdn) && hasEnoughParts);
	};

	var _invalidHostOrFQDNMessage = _('Invalid hostname or fully qualified domain name!<br/>Expected format: <i>myhost</i> or <i>hostname.mydomain.intranet</i>');
	var _validateHostOrFQDN = function(hostOrFQDN) {
		hostOrFQDN = hostOrFQDN || '';
		var acceptEmtpy = !hostOrFQDN && !this.required;
		return acceptEmtpy || _validateFQDN.call(this, hostOrFQDN)  || _validateHostname.call(this, hostOrFQDN);
	};

	var _regDN = /^(dc|cn|c|o|l)=[a-zA-Z0-9-]+(,(dc|cn|c|o|l)=[a-zA-Z0-9-]+)+$/;
	var _invalidLDAPBase = _("Invalid LDAP base!<br/>The LDAP base may neither contain blanks nor any special characters. Its structure needs to consist of at least two relative distinguished names (RDN) with attribute tags 'dc', 'cn', 'c', 'o', or 'l' (e.g., dc=test,dc=net).");
	var _validateLDAPBase = function(ldapBase) {
		ldapBase = ldapBase || '';
		var acceptEmtpy = !ldapBase && !this.required;
		return acceptEmtpy || _regDN.test(ldapBase);
	};

	// mappings to convert umlauts  and special basic latin letters to standard ones
	// basic latin letters with no real equivalent
	// 'Ð' U+00D0 - LATIN CAPITIAL LETTER ETH
	// 'Þ' U+00DE - LATIN CAPITAL LETTER THORN
	// 'ð' U+00F0 - LATIN SMALL LETTER ETH
	// 'þ' U+00FE - LATIN SMALL LETTER THORN
	var _umlauts = { 'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'Ae', 'Å': 'A', 'Æ': 'AE', 'Ç': 'C', 'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E', 'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I', 'Ð': 'D', 'Ñ': 'N', 'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'Oe', 'Ø': 'O', 'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'Ue', 'Ý': 'Y', 'Þ': 'P', 'ß': 'ss', 'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'ae', 'å': 'a', 'æ': 'ae', 'ç': 'c', 'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e', 'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i', 'ð': 'o', 'ñ': 'n', 'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'oe', 'ø': 'o', 'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'ue', 'ý': 'y', 'þ': 'p', 'ÿ': 'y'};

	var _replaceUmlauts = function(str) {
		var newStr = '';
		for (var i = 0; i < str.length; ++i) {
			newStr += _umlauts[str[i]] || str[i];
		}
		return newStr;
	};

	var _getDecoratedLanguageOptions = function() {
		return array.map(i18nTools.availableLanguages, function(_ilang) {
			var ilang = lang.mixin({
				country: _ilang.id.split('-')[1].toLowerCase(),
				value: _ilang.id
			}, _ilang);
			ilang.label = lang.replace('<span class="dijitReset dijitInline setupLangField">{label}</span>', ilang);
			return ilang;
		});
	};

	var _showTooltip = function(node, msg, evt) {
		Tooltip.show(msg, node);
		if (evt) {
			dojoEvent.stop(evt);
		}
		on.once(dojo.body(), 'click', function(evt) {
			Tooltip.hide(node);
			dojoEvent.stop(evt);
		});
	};

	var _alert = function(msg) {
		dialog.alert(msg, _('Validation error'));
	};

	return declare('setup.ApplianceWizard', Wizard, {
		// __systemsetup__ user is logged in at local firefox session
		local_mode: false,

		// original values as return by the load command
		values: {},

		// whether this wizard is started as part of the Debian Installer
		// or to configure an appliance image
		partOfInstaller: false,

		autoHeight: true,

		_checkStatusFileTimer: null,
		_checksTimedOut: 0,
		statusCheckResult: 'unknown',
		_joinTriggered: false,

		autoValidate: false,
		autoFocus: true,

		ucr: {},

		_gallery: null,
		_appGalleryUpdated: null,
		_nLocaleSettingsConfigured: false,
		_forcedPage: null,
		_progressBar: null,
		_criticalJoinErrorOccurred: false,
		_initialDHCPQueriesDeferred: null,
		_lastAppliedNetworkValues: null,

		disabledPages: null,
		disabledFields: null,

		_newFQDN: null, // temp variable for the guessed or actual FQDN; TODO: remove this

		postMixInProperties: function() {
			this.inherited(arguments);
			this.standbyColor = this.local_mode ? 'var(--document-bgc)' : this.standbyColor;
		},

		constructor: function(props) {
			lang.mixin(this, props);

			// customize some texts for an app appliance case
			var showPreconfiguredSetupOption = tools.isTrue(this.ucr['umc/web/appliance/fast_setup_mode']) && this.values.joined;
			var applianceName = '';
			var welcomeMessage = _('Welcome to Univention Corporate Server (UCS).');
			var welcomeHeader = _('UCS setup');
			var doneHeader = _('UCS setup successful');
			var errorHeader = _('UCS setup - An error occurred');
			var creatDomainLabel = _('Create a new UCS domain');
			var createDomainHelpTextContent = _('Configure this system as first system for the new domain. Additional systems can join the domain later.');
			var credentialsMasterEmailLabel = _('E-mail address to activate UCS');
			var credentialsMasterHelpText = _('<p>Enter the name of your organization, an e-mail address to activate UCS and a password for your <i>Administrator</i> account.</p><p>The password is mandatory, it will be used for the domain Administrator as well as for the local superuser <i>root</i>.</p>');
			if (this.ucr['umc/web/appliance/name']) {
				applianceName = this.ucr['umc/web/appliance/name'];
				welcomeMessage = _('Welcome to the setup of %s Appliance.', applianceName);
				welcomeHeader = _('%s Appliance', applianceName);
				doneHeader = _('Setup successful');
				errorHeader = _('Setup - An error occurred');
				creatDomainLabel = _('Manage users and permissions directly on this system');
				createDomainHelpTextContent = _('A new domain directory is created on this system. User and management data are stored locally.');
				credentialsMasterEmailLabel = _('E-mail address to activate %s Appliance', applianceName);
				credentialsMasterHelpText = _('<p>Enter the name of your organization, an e-mail address to activate %s Appliance and a password for your <i>Administrator</i> account.</p><p>The password is mandatory, it will be used for the domain Administrator as well as for the local superuser <i>root</i>.</p>', applianceName);
			}
			welcomeMessage += ' ' + _('A few questions are needed to complete the configuration process.');
			if (this.ucr['umc/web/appliance/logo']) {
				// override UCS logo with app logo on welcome page
				var logoURL = this.ucr['umc/web/appliance/logo'];
				if (logoURL.indexOf('/') !== 0) {
					// use path relative to dijit/themes/umc
					logoURL = require.toUrl('dijit/themes/umc/' + logoURL);
				}
				styles.insertCssRule('.umc-setup-page-welcome .umcPageIcon', lang.replace('background-image: url({0}) !important;', [logoURL]));
			}

			var pageConf = {
				navBootstrapClasses: 'col-xs-12 col-sm-4 col-md-4 col-lg-4',
				mainBootstrapClasses: 'col-xs-12 col-sm-8 col-md-8 col-lg-8'
			};

			this.pages = [lang.mixin({}, pageConf, {
				name: 'welcome',
				headerText: welcomeHeader,
				helpText: welcomeMessage,
				widgets: [{
					type: Select,
					name: '_language',
					label: _('Choose your language'),
					options: _getDecoratedLanguageOptions(),
					value: i18nTools.defaultLang(),
					onChange: lang.hitch(this, function(locale) {
						if (locale != i18nTools.defaultLang()) {
							this.onReload(locale);
						}
					}),
					size: 'One'
				}, {
					type: LiveSearch,
					name: '_search',
					store: new _CityStore({umcpCommand: lang.hitch(this, 'umcpCommand')}),
					label: _('Enter a city nearby to preconfigure settings such as timezone, system language, keyboard layout.'),
					inlineLabel: _('e.g., Boston...'),
					labelConf: {'class': 'umc-ucssetup-wizard-livesearch'}
				}, {
					type: TitlePane,
					'class': 'umc-ucssetup-wizard-city-details',
					name: 'result',
					content: '',
					title: _('Localization settings'),
					visible: false,
					toggleable: false
				}]
			}), lang.mixin({}, pageConf, {
				name: 'locale',
				headerText: _('Localization settings'),
				helpText: _('Choose your system\'s localization settings.'),
				widgets: [{
					type: ComboBox,
					name: 'locale/default',
					label: _('Default system locale'),
					value: 'en_US.UTF-8:UTF-8',
					umcpCommand: lang.hitch(this, 'umcpCommand'),
					dynamicOptions: {pattern: '*'},
					dynamicValues: 'setup/lang/locales'
				}, {
					type: ComboBox,
					name: 'timezone',
					label: _('Time zone'),
					value: 'America/New_York',
					umcpCommand: lang.hitch(this, 'umcpCommand'),
					dynamicValues: 'setup/lang/timezones'
				}, {
					type: ComboBox,
					name: 'xorg/keyboard/options/XkbLayout',
					label: _('Keyboard layout'),
					value: 'us',
					umcpCommand: lang.hitch(this, 'umcpCommand'),
					dynamicValues: 'setup/lang/keyboard/layout',
					onChange: lang.hitch(this, function(value) {
						if (this.local_mode && value) {
							this.umcpCommand('setup/keymap/save', {layout: value});
						}
					})
				}]
			}), lang.mixin({}, pageConf, {
				name: 'required_ram',
				headerText: _('<b>Warning:</b> Not enough available memory'),
				headerTextAllowHTML: true,
				helpText: _('The available memory is not sufficient.'),
				widgets: [{
					type: Text,
					name: 'required_ram',
					content: this._getMemoryWarning(applianceName),
				}]
			}), lang.mixin({}, pageConf, {
				name: 'license',
				headerText: _('License agreement'),
				helpText: _('Please read carefully the license agreement for %s Appliance.', applianceName || ''),
				widgets: [{
					type: Text,
					'class': 'umcUCSSetupLicenseAgreement',
					name: 'license',
					content: this.values.license_agreement
				}]
			}), lang.mixin({}, pageConf, {
				name: 'network',
				headerText: _('Domain and network configuration'),
				helpText: _('Specify the network settings for this system.'),
				layout: [
					['_dhcp', '_renewLease'],
					['_ip0', '_netmask0'],
					['_ip1', '_netmask1'],
					['_ip2', '_netmask2'],
					['_ip3', '_netmask3'],
					'gateway',
					['nameserver1', 'nameserver2'],
					'proxy/http',
					'configureProxySettings'
				],
				widgets: [{
					type: Text,
					name: '_renewLease',
					label: '<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').dhclient();">' + _('(Request address again)') + '</a>',
					content: '',
					visible: false
				}, {
					type: CheckBox,
					name: '_dhcp',
					label: _('Obtain IP address automatically (DHCP)'),
					onChange: lang.hitch(this, function(value) {
						this._disableNetworkAddressWidgets(value);
						this.getWidget('network', '_renewLease').set('visible', value);
						var focused = this.getWidget('network', '_dhcp').focused;
						if (value && focused) {
							// see whether DHCP is working
							this.dhclient();
						}
					})
				}, {
					type: TextBox,
					name: '_ip0',
					label: _('IPv4/IPv6 address {interface}'),
					inlineLabel: '',
					value: '',
					onChange: lang.hitch(this, '_updateNetwork', 0),
					invalidMessage: _invalidIPAddressMessage,
					validator: _validateIPAddress
				}, {
					type: TextBox,
					name: '_netmask0',
					label: _('IPv4 net mask/IPv6 prefix {interface}'),
					inlineLabel: '',
					invalidMessage: _invalidNetmaskAndPrefixMessage,
					validator: _validateNetmaskAndPrefix
				}, {
					type: TextBox,
					name: '_ip1',
					label: _('IPv4/IPv6 address {interface}'),
					inlineLabel: '',
					value: '',
					visible: false,
					onChange: lang.hitch(this, '_updateNetwork', 1),
					invalidMessage: _invalidIPAddressMessage,
					validator: _validateIPAddress
				}, {
					type: TextBox,
					name: '_netmask1',
					label: _('IPv4 net mask/IPv6 prefix {interface}'),
					inlineLabel: '',
					visible: false,
					invalidMessage: _invalidNetmaskAndPrefixMessage,
					validator: _validateNetmaskAndPrefix
				}, {
					type: TextBox,
					name: '_ip2',
					label: _('IPv4/IPv6 address {interface}'),
					inlineLabel: '',
					visible: false,
					value: '',
					onChange: lang.hitch(this, '_updateNetwork', 2),
					invalidMessage: _invalidIPAddressMessage,
					validator: _validateIPAddress
				}, {
					type: TextBox,
					name: '_netmask2',
					label: _('IPv4 net mask/IPv6 prefix {interface}'),
					inlineLabel: '',
					visible: false,
					invalidMessage: _invalidNetmaskAndPrefixMessage,
					validator: _validateNetmaskAndPrefix
				}, {
					type: TextBox,
					name: '_ip3',
					label: _('IPv4/IPv6 address {interface}'),
					inlineLabel: '',
					visible: false,
					value: '',
					onChange: lang.hitch(this, '_updateNetwork', 3),
					invalidMessage: _invalidIPAddressMessage,
					validator: _validateIPAddress
				}, {
					type: TextBox,
					name: '_netmask3',
					label: _('IPv4 net mask/IPv6 prefix {interface}'),
					inlineLabel: '',
					visible: false,
					invalidMessage: _invalidNetmaskAndPrefixMessage,
					validator: _validateNetmaskAndPrefix
				}, {
					type: TextBox,
					name: 'gateway',
					label: _('Gateway'),
					invalidMessage: _invalidIPAddressMessage,
					validator: _validateIPAddress
				}, {
					type: TextBox,
					name: 'nameserver1',
					label: _('Preferred DNS server'),
					invalidMessage: _invalidIPAddressMessage,
					validator: _validateIPAddress
				}, {
					type: TextBox,
					name: 'nameserver2',
					label: _('Alternate DNS server'),
					invalidMessage: _invalidIPAddressMessage,
					validator: _validateIPAddress
				}, {
					type: Text,
					name: 'configureProxySettings',
					label: '<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').configureProxySettings();">' +
						_('(configure proxy settings)') +
						'</a>',
					content: ''
				}, {
					type: TextBox,
					name: 'proxy/http',
					label: _('HTTP proxy') +
						' (<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').showTooltip(event, \'proxy\');">' +
						_('more information') +
						'</a>)',
					visible: false
				}]
			}), lang.mixin({}, pageConf, {
				name: 'role',
				headerText: _('Domain setup'),
				helpText: _('Please select your domain settings.'),
				widgets: [{
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_preconfiguredDomain',
					label: _('Fast demo configuration'),
					checked: true,
					labelConf: {'class': 'umc-ucssetup-wizard-radio-button-label'},
					visible: showPreconfiguredSetupOption,
					disabled: !showPreconfiguredSetupOption
				}, {
					type: Text,
					name: 'preconfiguredDomainHelpText',
					content: _('Quick setup of a system for testing purposes. Several system configurations are predefined and cannot be changed at a later point.'),
					labelConf: {'class': 'umc-ucssetup-wizard-indent'},
					visible: showPreconfiguredSetupOption
				}, {
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_createDomain',
					label: creatDomainLabel,
					checked: true,
					labelConf: {'class': 'umc-ucssetup-wizard-radio-button-label'}
				}, {
					type: Text,
					name: 'createDomainHelpText',
					content: createDomainHelpTextContent,
					labelConf: {'class': 'umc-ucssetup-wizard-indent'}
				}, {
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_joinDomain',
					label: _('Join into an existing UCS domain'),
					labelConf: {'class': 'umc-ucssetup-wizard-radio-button-label'}
				}, {
					type: Text,
					name: 'joinDomainHelpText',
					content: _('Use this option if you already have one or more UCS systems.'),
					labelConf: {'class': 'umc-ucssetup-wizard-indent'}
				}, {
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_adDomain',
					label: _('Join into an existing Microsoft Active Directory domain'),
					labelConf: {'class': 'umc-ucssetup-wizard-radio-button-label'}
				}, {
					type: Text,
					name: 'adDomainHelpText',
					content: _('This system will become part of an existing non-UCS Active Directory domain.'),
					labelConf: {'class': 'umc-ucssetup-wizard-indent'}
				}, {
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_noDomain',
					label: _('Do not use any domain'),
					labelConf: {'class': 'umc-ucssetup-wizard-radio-button-label'}
				}, {
					type: Text,
					name: 'noDomainHelpText',
					content: _('This should only be used in rare use cases, for example as firewall systems.'),
					labelConf: {'class': 'umc-ucssetup-wizard-indent'}
				}, {
					type: Text,
					name: 'ifUnsureHelpText',
					content: _('If unsure, select <i>%s</i>.', creatDomainLabel),
					labelConf: {'class': 'umc-ucssetup-wizard-radio-button-label'}
				}]
			}), lang.mixin({}, pageConf, {
				name: 'role-nonmaster-ad',
				headerText: _('System role'),
				helpText: _('Specify the type of this system.'),
				widgets: [{
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_roleBackup',
					label: _('Domain controller backup'),
					checked: true,
					labelConf: {'class': 'umc-ucssetup-wizard-radio-button-label'}
				}, {
					type: Text,
					name: 'helpBackup',
					content: _('A DC backup is the fallback system for the UCS DC master and can take over the role of the DC master permanently. It is recommended to use at least one DC backup in the domain.'),
					labelConf: {'class': 'umc-ucssetup-wizard-indent'}
				}, {
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_roleSlave',
					label: _('Domain controller slave'),
					labelConf: {'class': 'umc-ucssetup-wizard-radio-button-label'}
				}, {
					type: Text,
					name: 'helpSlave',
					content: _('DC slave systems are ideal for site servers, they provide authentication services for the domain. Local services running on a DC slave can access the local LDAP database.'),
					labelConf: {'class': 'umc-ucssetup-wizard-indent'}
				}, {
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_roleMember',
					label: _('Member server'),
					labelConf: {'class': 'umc-ucssetup-wizard-radio-button-label'}
				}, {
					type: Text,
					name: 'helpMember',
					content: _('Member servers should be used for services which do not need a local authentication database, for example for file or print servers.'),
					labelConf: {'class': 'umc-ucssetup-wizard-indent'}
				}]
			}), lang.mixin({}, pageConf, {
				name: 'credentials-master',
				headerText: _('Account information'),
				helpText: credentialsMasterHelpText,
				layout: [
					'organization',
					'email_address',
					'_user_account',
					'root_password'
				],
				widgets: [{
					type: TextBox,
					name: 'organization',
					label: _('Organization name'),
					onChange: lang.hitch(this, '_updateOrganizationName')
				}, {
					type: VirtualKeyboardBox,
					chars: ['-', '_', '.', '@'],
					name: 'email_address',
					label: credentialsMasterEmailLabel +
						' (<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').showTooltip(event, \'email\');">' +
						_('more information') +
						'</a>)',
					validator: _validateEmailAddress,
					invalidMessage: _invalidEmailAddressMessage
				}, {
					type: Text,
					name: '_user_account',
					'class': 'umcAccountInfoText',
					content: _('Fill in the password for the system administrator user <b>root</b> and the domain administrative user account <b>Administrator</b>.')
				}, {
					type: PasswordInputBox,
					required: true,
					name: 'root_password',
					label: _('Password')
				}]
			}), lang.mixin({}, pageConf, {
				name: 'credentials-ad',
				headerText: _('Active Directory join information'),
				helpText: _('Enter name and password of a user account which is authorised to join a system into this domain.'),
				widgets: [{
					type: TextBox,
					name: 'ad/address',
					label: _('Address of Active Directory domain controller or name of Active Directory domain'),
					required: true
				}, {
					type: TextBox,
					name: 'ad/username',
					label: _('Username'),
					value: 'Administrator',
					required: true
				}, {
					type: PasswordBox,
					name: 'ad/password',
					label: _('Password'),
					required: true
				}]
			}), lang.mixin({}, pageConf, {
				name: 'credentials-nonmaster',
				headerText: _('Domain join information'),
				helpText: _('Enter name and password of a user account which is authorised to join a system into this domain.'),
				widgets: [{
					type: CheckBox,
					name: 'start/join',
					label: _('Start join at the end of the installation'),
					value: true,
					disabled: !!this.ucr['umc/web/appliance/name'],
					onChange: lang.hitch(this, function(value) {
						this.getWidget('credentials-nonmaster', '_ucs_autosearch_master').set('disabled', !value);
						this.getWidget('credentials-nonmaster', '_ucs_address').set('disabled', !value || this.getWidget('credentials-nonmaster', '_ucs_autosearch_master').get('value'));
						this.getWidget('credentials-nonmaster', '_ucs_user').set('disabled', !value);
						this.getWidget('credentials-nonmaster', '_ucs_password').set('disabled', !value);
					})
				}, {
					type: CheckBox,
					name: '_ucs_autosearch_master',
					label: _('Search Domain controller master in DNS'),
					value: true,
					onChange: lang.hitch(this, function(value) {
						this.getWidget('credentials-nonmaster', '_ucs_address').set('disabled', value);
					})
				}, {
					type: TextBox,
					name: '_ucs_address',
					label: _('Hostname of the domain controller master'),
					required: true,
					disabled: true,
					validator: _validateFQDN,
					invalidMessage: _invalidFQDNMessage
				}, {
					type: TextBox,
					name: '_ucs_user',
					label: _('Username'),
					value: 'Administrator',
					required: true
				}, {
					type: PasswordBox,
					name: '_ucs_password',
					label: _('Password'),
					required: true
				}]
			}), lang.mixin({}, pageConf, {
				name: 'warning-basesystem',
				headerText: _('No domain warning'),
				helpText: _('The installed UCS system will not offer any web-based domain management functions and will not be able to be a domain member. Such an UCS system should only be used in some rare use cases, for example as firewall system.')
			}), lang.mixin({}, pageConf, {
				name: 'fqdn-master',
				headerText: _('Host settings'),
				helpText: _('Specify the name of this system.'),
				layout: [
					['_hostname', '_domainname'], // for docker only!
					['_fqdn', 'ldap/base']
				],
				widgets: [{
					type: TextBox,
					name: '_hostname',
					label: _('Hostname (unchangeable. Was set while creating the container)'),
					disabled: true,
					visible: false,
					validator: _validateHostname,
					invalidMessage: _invalidHostOrFQDNMessage
				}, {
					type: TextBox,
					name: '_domainname',
					label: _('Domain name'),
					disabled: true,
					visible: false,
					required: true,
					onChange: lang.hitch(this, function(value) {
						var fqdn = 'dummy.' + value;
						this._updateLDAPBase(fqdn);
					}),
					validator: _validateDomainName,
					invalidMessage: _invalidDomainNameMessage
				}, {
					type: TextBox,
					name: '_fqdn',
					label: _('Fully qualified domain name'),
					required: true,
					onChange: lang.hitch(this, '_updateLDAPBase'),
					validator: _validateFQDN,
					invalidMessage: _invalidFQDNMessage
				}, {
					type: TextBox,
					name: 'ldap/base',
					label: _('LDAP base'),
					required: true,
					validator: _validateLDAPBase,
					invalidMessage: _invalidLDAPBase
				}]
			}), lang.mixin({}, pageConf, {
				name: 'fqdn-nonmaster-all',
				headerText: _('Host settings'),
				helpText: _('Specify the name of this system.'),
				layout: [
					'hostname',
					'root_password'
				],
				widgets: [{
					type: TextBox,
					name: 'hostname',
					label: _('Hostname or fully qualified domain name') +
						' (<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').showTooltip(event, \'hostname\');">' +
						_('more information') +
						'</a>)',
					required: true,
					validator: _validateHostOrFQDN,
					invalidMessage: _invalidHostOrFQDNMessage
				}, {
					type: PasswordInputBox,
					name: 'root_password',
					label: _('Local root password'),
					required: this.local_mode
				}]
			}), lang.mixin({}, pageConf, {
				name: 'schooldomain-slave',
				headerText: _('Server role inside the UCS@school domain'),
				helpText: _('Choose which role this server is supposed to take in your UCS@school domain.'),
				widgets: [{
					type: RadioButton,
					radioButtonGroup: 'schoolrole',
					name: '_schoolRoleEducational',
					label: _('School server of the educational network'),
					checked: true,
					labelConf: {'class': 'umc-ucssetup-wizard-radio-button-label'}
				}, {
					type: Text,
					name: 'helpEducational',
					content: _('The server will provide educational UCS@school services for a school, e.g. exam mode.'),
					labelConf: {'class': 'umc-ucssetup-wizard-indent'}
				}, {
					type: RadioButton,
					radioButtonGroup: 'schoolrole',
					name: '_schoolRoleAdministrative',
					label: _('School server of the administrative network'),
					labelConf: {'class': 'umc-ucssetup-wizard-radio-button-label'}
				}, {
					type: Text,
					name: 'helpAdministrative',
					content: _('The server will only provide domain services to a school\'s administrative network, not educational UCS@school services.'),
					labelConf: {'class': 'umc-ucssetup-wizard-indent'}
				}, {
					type: RadioButton,
					radioButtonGroup: 'schoolrole',
					name: '_schoolRoleCentral',
					label: _('Central server'),
					labelConf: {'class': 'umc-ucssetup-wizard-radio-button-label'}
				}, {
					type: Text,
					name: 'helpCentral',
					content: _('The server will not be assigned to a specific school and will not provide UCS@school services.'),
					labelConf: {'class': 'umc-ucssetup-wizard-indent'}
				}]
			}), lang.mixin({}, pageConf, {
				name: 'software',
				headerText: _('Software configuration'),
				helpText: _('<p>Select UCS software components for installation on this system. This step can be skipped; the components are also available in the Univention App Center in the category <i>UCS components</i>.</p><p>Third-party software (e.g., groupware) is also available through the Univention App Center.</p>')
			}), lang.mixin({}, pageConf, {
				name: 'validation',
				headerText: _('Validation failed'),
				helpText: _('The following entries could not be validated:'),
				widgets: [{
					type: Text,
					name: 'info',
					content: ''
				}]
			}), lang.mixin({}, pageConf, {
				name: 'summary',
				headerText: _('Confirm configuration settings'),
				helpText: _('Please confirm the chosen configuration settings which are summarized in the following.'),
				widgets: [{
					type: Text,
					name: 'info',
					content: ''
				}, {
					type: CheckBox,
					name: 'update/system/after/setup',
					size: 'Two',
					value: true,
					label: _('Update system after setup') +
						' (<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').' +
						'showTooltip(event, \'updates\');">' + _('more information') + '</a>)'
				}, {
					type: Text,
					name: 'privacyStatement',
					content: ''
				}]
			}), lang.mixin({}, pageConf, {
				name: 'error',
				headerText: errorHeader,
				helpText: '_',
				widgets: [{
					type: ContainerWidget,
					name: 'errors',
					style: 'width: 100%'
				}, {
					type: Text,
					name: 'info',
					content: ''
				}]
			}), lang.mixin({}, pageConf, {
				name: 'done',
				headerText: doneHeader,
				helpTextRegion: 'main',
				helpText: '_',
				widgets: []
			})];
			array.forEach(this.pages, function(page) {
				page['class'] = 'umc-setup-page umc-setup-page-' + page.name;
			});
		},

		_isDHCPPreConfigured: function() {
			return array.some(this._getNetworkDevices(), function(idev) {
				var dev = this.values.interfaces[idev];
				return dev && dev.ip4dynamic;
			}, this);
		},

		postCreate: function() {
			this.inherited(arguments);

			tools.forIn(this._pages, function(name, page) {
				page.addChild(new Text({
					'class': 'umcPageIcon',
					region: 'nav'
				}));
			});
			// DO NOT set the widgets in appliance mode
			// as the pre-configured network properties do not make sense there
			// exception: DHCP
			var isDHCP = this._isDHCPPreConfigured();
			if (isDHCP || this.partOfInstaller) {
				this.getWidget('network', '_dhcp').set('value', isDHCP);
				array.forEach(this._getNetworkDevices(), function(idev, i) {
					var dev = this.values.interfaces[idev];
					var old = ['', ''];
					if (dev) {
						old = dev.ip4[0] || dev.ip6[0] || ['', ''];
					}
					this.getWidget('network', '_ip' + i).set('value', old[0]);
					this.getWidget('network', '_netmask' + i).set('value', old[1]);
				}, this);
				this.getWidget('network', 'gateway').set('value', this.values.gateway);
				this.getWidget('network', 'nameserver1').set('value', this.values.nameserver1);
			}
			if (this._isDocker()) {
				this.getWidget('fqdn-nonmaster-all', 'hostname').set('value', this.values.hostname);
				this.getWidget('fqdn-master', '_hostname').set('value', this.values.hostname);
				this.getWidget('fqdn-master', '_domainname').set('value', this.values.domainname);
			}
		},

		_adjustWizardHeight: function() {
			var _setVisibility = lang.hitch(this, function(visible) {
				array.forEach(this._getNetworkDevices(), function(idev, i) {
					this.getWidget('network', '_ip' + i).set('visible', visible);
					this.getWidget('network', '_netmask' + i).set('visible', visible);
				}, this);
				this.getWidget('license', 'license').set('visible', visible);
			});

			// ignore number of network interfaces when determining the auto height
			_setVisibility(false);
			this.inherited(arguments);
			_setVisibility(true);
		},

		_areRolesDisabled: function() {
			return array.every(arguments, function(irole) {
				return array.indexOf(this.disabledFields, irole) >= 0;
			}, this);
		},

		_evaluateBlacklist: function() {
			var disable = [];
			array.forEach(this.disabledFields, lang.hitch(this, function(field) {
				if (field == 'password') {
					disable.push(['fqdn-nonmaster-all', 'root_password']);
					disable.push(['credentials-master', 'root_password']);
					disable.push(['credentials-master', '_user_account']);
					this.getPage('credentials-master').set('helpText', _('<p>Enter the name of your organization and an e-mail address to activate UCS.</p>'));
				} else if (field == 'network') {
					disable.push(['network', '_dhcp']);
					disable.push(['network', '_ip0']);
					disable.push(['network', '_netmask0']);
					disable.push(['network', '_ip1']);
					disable.push(['network', '_netmask1']);
					disable.push(['network', '_ip2']);
					disable.push(['network', '_netmask2']);
					disable.push(['network', '_ip3']);
					disable.push(['network', '_netmask3']);
					disable.push(['network', 'gateway']);
				} else if (field == 'nameservers') {
					disable.push(['network', 'nameserver1']);
					disable.push(['network', 'nameserver2']);
				} else if (field == 'proxy') {
					disable.push(['network', 'proxy/http']);
					disable.push(['network', 'configureProxySettings']);
				} else if (field == 'hostname') {
					this.getWidget('fqdn-nonmaster-all', 'hostname').set('disabled', true);
					this.getWidget('fqdn-master', '_hostname').set('visible', true);
					this.getWidget('fqdn-master', '_domainname').set('visible', true);
					this.getWidget('fqdn-master', '_domainname').set('disabled', false);
					disable.push(['fqdn-master', '_fqdn']);
				} else if (field == 'locale') {
					disable.push(['welcome', '_language']);
					disable.push(['welcome', '_search']);
					disable.push(['welcome', 'result']);
					disable.push(['locale', 'locale/default']);
					disable.push(['locale', 'xorg/keyboard/options/XkbLayout']);
					disable.push(['locale', 'timezone']);
				} else if (field == 'basesystem') {
					disable.push(['role', '_noDomain']);
					disable.push(['role', 'noDomainHelpText']);
				} else if (field == 'ad') {
					disable.push(['role', '_adDomain']);
					disable.push(['role', 'adDomainHelpText']);
				} else if (field == 'preconfigured_system') {
					disable.push(['role', '_preconfiguredDomain']);
					disable.push(['role', 'preconfiguredDomainHelpText']);
				} else if (field == 'domaincontroller_backup') {
					disable.push(['role-nonmaster-ad', '_roleBackup']);
					disable.push(['role-nonmaster-ad', 'helpBackup']);
				} else if (field == 'domaincontroller_slave') {
					disable.push(['role-nonmaster-ad', '_roleSlave']);
					disable.push(['role-nonmaster-ad', 'helpSlave']);
				} else if (field == 'memberserver') {
					disable.push(['role-nonmaster-ad', '_roleMember']);
					disable.push(['role-nonmaster-ad', 'helpMember']);
				}
			}));

			if (this._areRolesDisabled('domaincontroller_backup', 'domaincontroller_slave', 'memberserver')) {
				// hide option to join a UCS domain
				disable.push(['role', '_joinDomain']);
				disable.push(['role', 'joinDomainHelpText']);
			}

			array.forEach(disable, lang.hitch(this, function(page_widget) {
				var widget = this.getWidget(page_widget[0], page_widget[1]);
				if (widget) {
					widget.set('visible', false);
					widget.set('disabled', true);
				}
			}));
		},

		_preselectFirstVisibleRadioButton: function() {
			array.forEach(['role', 'role-nonmaster-ad'], function(_ipage) {
				var ipage = this.getPage(_ipage);
				array.some(ipage._form.widgets, function(_iwidget) {
					var iwidget = this.getWidget(_ipage, _iwidget.name);
					if (iwidget.isInstanceOf(RadioButton) && iwidget.get('visible')) {
						iwidget.set('value', true);
						return true;
					}
				}, this);
			}, this);
		},

		_sendDHCPQueries: function() {
			// send out queries for each network device
			var queries = {};
			array.forEach(this._getNetworkDevices(), function(idev, i) {
				// workaround: use umcpProgressCommand() to make the setup/net/dhclient threaded
				queries[idev] = this.umcpProgressCommand(this._progressBar, 'setup/net/dhclient', {
					'interface': idev
				}, false).then(null, function() {
					// catch error case to avoid dojo/promise/all canceling all bundled deferreds
					return {};
				});
			}, this);

			return queries;
		},

		_processDHCPQueries: function(queries) {
			// generate mapping from device name to index
			var dev2index = {};
			array.forEach(this._getNetworkDevices(), function(idev, i) {
				// workaround: use umcpProgressCommand() to make the setup/net/dhclient threaded
				dev2index[idev] = i;
			});

			// blur current element
			tools.defer(function() {
				if (focusUtil.curNode) { focusUtil.curNode.blur(); }
			}, 200);

			this.standbyDuring(all(queries)).then(lang.hitch(this, function(response) {
				var hasDHCP = false;
				var gateway = null;
				var nameserver = null;
				tools.forIn(response, function(idev, result) {
					var i = dev2index[idev];
					var address = result[idev + '_ip'];
					var netmask = result[idev + '_netmask'];
					if (!address && !netmask) {
						// reset ip/mask values
						this.getWidget('network', '_ip' + i).reset();
						this.getWidget('network', '_netmask' + i).reset();
						return;
					}

					// at least for one device DHCP did work :)
					hasDHCP = true;

					// handle gateway/nameserver values
					gateway = gateway || result.gateway;
					nameserver = nameserver || result.nameserver_1;

					// set received values
					this.getWidget('network', '_ip' + i).set('value', address);
					this.getWidget('network', '_netmask' + i).set('value', netmask);
				}, this);

				// set received gateway/nameserver values
				if (gateway) {
					this.getWidget('network', 'gateway').set('value', gateway);
				}
				if (nameserver) {
					this.getWidget('network', 'nameserver1').set('value', nameserver);
				}

				// did DHCP work?
				if (!hasDHCP) {
					dialog.alert(_('DHCP query failed.'));
					this.getWidget('network', '_dhcp').set('value', false);
				}
			}));
		},

		dhclient: function() {
			var queries = this._sendDHCPQueries();
			this._processDHCPQueries(queries);
		},

		_disableNetworkAddressWidgets: function(disable) {
			for (var idx = 0; idx < 4; ++idx) {
				this.getWidget('network', '_ip' + idx).set('disabled', disable);
				this.getWidget('network', '_netmask' + idx).set('disabled', disable);
			}
			this.getWidget('network', 'gateway').set('disabled', disable);
		},

		configureProxySettings: function() {
			this.getWidget('network', 'proxy/http').set('visible', true);
			this.getWidget('network', 'configureProxySettings').set('visible', false);
		},

		showTooltip: function(evt, type) {
			var msg = '';
			if (type == 'email') {
				if (this.ucr['umc/web/appliance/name']) {
					msg = _('A valid e-mail address is required to activate %s Appliance. The address can be specified now or also at a later point in time. An e-mail with a personalized license key will then be sent to your e-mail address. This license can be uploaded after the setup process.', this.ucr['umc/web/appliance/name']);
				} else {
					msg = _('A valid e-mail address allows to activate the UCS system for using the Univention App Center. The address can be specified now or also at a later point in time. An e-mail with a personalized license key will then be sent to your e-mail address. This license can be uploaded via the license dialog in Univention Management Console.');
				}
			}
			else if (type == 'hostname') {
				msg = _('For a specified host name, the domain name is automatically derived from the domain name server. A fully qualified domain may be necessary for mail server setups with differing domains.<br/>Note that the domain name <b>cannot</b> be changed after the UCS setup wizard has been completed.');
			}
			else if (type == 'proxy') {
				msg = _('A proxy address needs to be specified in the format: <i>http://proxy.mydomain.intranet:3128</i><br/>Proxy access with username and password may be specified via the format: <i>http://username:password@proxy.mydomain.intranet:3128</i>');
			}
			else if (type == 'updates') {
				msg = _('Install the latest errata and app updates after the setup.');
				if (this._isRoleMaster()) {
					msg = _('Install the latest patch level, errata and app updates after the setup.');
				} else if (this._isRoleNonMaster()) {
					msg = _('Update system to the UCS release version of the master domain controller and install all available errata and app updates after the setup.');
				}
			}
			if (msg) {
				_showTooltip(evt.target, msg, evt);
			}
		},

		_getMemoryWarning: function(applianceName) {
			var memory_min = Math.max(parseInt(this.ucr['system/setup/boot/minimal_memory'], 10) || 0, 2048);

			// The reported total memory is always a bit lower, than the actually installed amount:
			var memory_total_plus_margin = this.values.memory_total * 1.1;

			if (memory_min > memory_total_plus_margin) {
				var _memString = function(memory) {
					if (memory < 1024) {
						return _('%s MiB', parseInt(memory));
					}
					return _('%s GiB', parseInt(memory / 1024));
				};
				var message = lang.replace(
					_('At least {memory_min} RAM is required for the installation of {product_name}.') + ' ' +
					_('This system only has {memory_total} RAM.') + ' ' + _('Continuing the installation might lead to a non-functional system.') + ' ' +
					_('For further information please look at https://help.univention.com/t/13595.'), {
					memory_min: _memString(memory_min),
					memory_total: _memString(this.values.memory_total),
					product_name: applianceName || _('Univention Corporate Server')
				});
				return message;
			}
		},

		_addWidgetToPage: function(pageName, widget) {
			var page = this.getPage(pageName);
			if (page._form) {
				page.removeChild(page._form);
			}
			if (!widget.region) {
				widget.region = 'main';
			}
			page.addChild(widget);
		},

		_setupCitySearch: function() {
			var searchWidget = this.getWidget('welcome', '_search');
			searchWidget.watch('item', lang.hitch(this, function(attr, oldval, newval) {
				this._updateCityInfo(newval);
			}));
		},

		_setupJavaScriptLinks: function() {
			array.forEach([
					['network', 'configureProxySettings'],
					['network', '_renewLease'],
					['credentials-master', 'email_address'],
					['fqdn-nonmaster-all', 'hostname'],
					['network', 'proxy/http'],
					['summary', 'update/system/after/setup']
				], function(iitem) {
				var iwidget = this.getWidget(iitem[0], iitem[1]);
				iwidget.set('label', lang.replace(iwidget.label, this));
			}, this);
		},

		_getAppQuery: function() {
			var serverRole = this._getRole();
			var query = {
				// make sure that all software components are allowed for the
				// specified server role
				server_role: {
					test: function(val) {
						return serverRole != 'basesystem' && (!val.length || array.indexOf(val, serverRole) >= 0);
					}
				}
			};

			if (serverRole != 'domaincontroller_master') {
				// hide entries that need to install packages on the DC master
				query.default_packages_master = {
					test: function(val) {
						return !val.length;
					}
				};
			}

			if (this._isAdMember()) {
				query.ad_member_issue_hide = {
					test: function(val) {
						return !val;
					}
				};
			}

			return query;
		},

		_setupAppGallery: function() {
			this._apps = new Observable(new Memory({}));
			this._gallery = new _Grid({
				moduleStore: this._apps,
				columns: [{
					name: 'name',
					width: '100%',
					label: _('Software component'),
					formatter: lang.hitch(this, function(value, idx) {
						var item = this._gallery._grid.getItem(idx);
						return lang.replace('<div class="umcAppEntry"><div class="umcAppName">{name}</div><div class="umcAppDescription">{description}</div><div class="umcInfoIcon"></div></div>', item);
					})
				}],
				query: {id:"*"},
				'class': 'umcUCSSetupSoftwareGrid',
				footerFormatter: function(nItems) {
					if (!nItems) {
						return _('No additional software component will be installed.');
					}
					if (nItems == 1) {
						return _('Installation of one additional software component.', nItems);
					}
					return _('Installation of %d additional software components.', nItems);
				},
				standby: function() {},
				gridOptions: {
					className: '',
					selectionMode: 'toggle'
				}
			});

			var _handleSelectDefault = this._gallery._grid._handleSelect;
			this._gallery._grid._handleSelect = lang.hitch(this, function(evt) {
				if (!domClass.contains(evt.target, 'umcInfoIcon')) {
					// make sure the selection is not modified
					// when clicking on the info icon
					_handleSelectDefault.apply(this._gallery._grid, arguments);
				}
			});
			this._addWidgetToPage('software', this._gallery);
			this._gallery.on('filterDone', lang.hitch(this, function() {
				this._apps.query({is_installed: true}).forEach(lang.hitch(this, function(iitem) {
					//TODO: uncomment these lines, getItemIndex() was undefined
					//var idx = this._gallery._grid.getItemIndex(iitem);
					//this._gallery._grid.selection.addToSelection(idx);
				}));
			}));
			this._gallery._grid.on('.umcInfoIcon:click', lang.hitch(this, function(evt) {
				var row = this._gallery._grid.row(evt);
				_showTooltip(evt.target, entities.decode(row.data.long_description), evt);
				evt.stopPropagation();
				return false;
			}));
			this.umcpCommand('setup/apps/query').then(lang.hitch(this, function(response) {
				array.forEach(response.result, function(iitem) {
					this._apps.put(iitem);
				}, this);
				this._gallery.filter(this._getAppQuery());
			}));
		},

		_getNetworkDevices: function() {
			var devices = this.values.physical_interfaces;
			if (!devices || !devices.length) {
				// This should not happen!
				// There should always be at least one network device!
				console.error('No network interface could be detected! Assuming there is one interface named "eth0".');
				devices = ['eth0'];
			}
			devices.sort();
			// return only the first 4 physical interfaces because we only have 4 ip widgets
			devices = devices.slice(0, 4);

			return devices;
		},

		_setupNetworkDevices: function() {
			var devices = this._getNetworkDevices();
			array.forEach(devices, function(idev, i) {
				var ipWidget = this.getWidget('network', '_ip' + i);
				var maskWidget = this.getWidget('network', '_netmask' + i);
				var conf = { 'interface': '(' + idev + ')' };
				if (devices.length == 1) {
					// do not show the device name if there is only one network device
					conf = { 'interface': '' };
				}
				ipWidget.set('label', lang.replace(ipWidget.get('label'), conf));
				ipWidget.set('visible', true);
				maskWidget.set('label', lang.replace(maskWidget.get('label'), conf));
				maskWidget.set('visible', true);
			}, this);
		},

		_setupFooterButtons: function() {
			// change labels of footer buttons on particular pages
			var buttons = this._pages.summary._footerButtons;
			buttons.next.set('label', _('Configure system'));
			buttons = this._pages.error._footerButtons;
			buttons.previous.set('label', _('Reconfigure'));
			buttons.finish.set('label', _('Finish'));
			buttons = this._pages.required_ram._footerButtons;
			buttons.next.set('label', _('Ignore'));
			this._pages.done._footerButtons.next.set('label', _('Finish'));
		},

		_setLocaleValues: function(data) {
			if (data.timezone) {
				this.getWidget('locale', 'timezone').setInitialValue(data.timezone);
			}
			if (data.locale) {
				this.getWidget('locale', 'locale/default').setInitialValue(data.locale);
			}
			if (data.keyboard) {
				this.getWidget('locale', 'xorg/keyboard/options/XkbLayout').setInitialValue(data.keyboard);
			}
		},

		_setLocaleDefault: function() {
			var defaults = {
				'de-DE': {
					timezone: 'Europe/Berlin',
					locale: 'de_DE.UTF-8:UTF-8',
					keyboard: 'de'
				},
				'de-AT': {
					timezone: 'Europe/Vienna',
					locale: 'de_AT.UTF-8:UTF-8',
					keyboard: 'at'
				},
				'de-CH': {
					timezone: 'Europe/Zurich',
					locale: 'de_CH.UTF-8:UTF-8',
					keyboard: 'ch'
				},
				'en-US': {
					timezone: 'America/New_York',
					locale: 'en_US.UTF-8:UTF-8',
					keyboard: 'us'
				},
				'en-GB': {
					timezone: 'Europe/London',
					locale: 'en_GB.UTF-8:UTF-8',
					keyboard: 'gb'
				}
			};
			this._setLocaleValues(defaults[i18nTools.defaultLang()] || {});
		},

		_initStatusCheck: function() {
			// timer to check the join status via existence of status file
			var piwikLoadTriggered = false;
			var checkLicenseAndLoadPiwik = lang.hitch(this, function() {
				if (piwikLoadTriggered || !this._joinTriggered) {
					return;
				}
				tools.loadMetaData().then(lang.hitch(this, function(data) {
					// verify whether a valid system UUID has been generated for the system
					var hasLicenseBase = data.has_license_base || this._isRoleBaseSystem();
					var isReady = hasLicenseBase && data.has_system_uuid;
					if (!isReady) {
						return;
					}

					// the system UUID has been generated -> trigger piwik
					piwikLoadTriggered = true;
					if (!data.piwikDisabled) {
						topic.publish('/umc/piwik/load', true);
					}
				}));
			});
			this._checkStatusFileTimer = new timing.Timer(1000 * 10);
			this._checkStatusFileTimer.onStart = lang.hitch(this, function() {
				this.set('statusCheckResult', 'unknown');
				this._checksTimedOut = 0;
			});
			this._checkStatusFileTimer.onTick = lang.hitch(this, function() {
				checkLicenseAndLoadPiwik();
				var _statusFileURI = '/ucs_setup_process_status.json';
				request(_statusFileURI, {
					timeout: 1000,
					handleAs: 'json',
					preventCache: true
				}).then(lang.hitch(this, function(text) {
					// file exists -> setup process has been triggered
					this.set('statusCheckResult', text);
					this._checksTimedOut = 0;
				}), lang.hitch(this, function(err) {
					// file does not exist...
					var reqStatus = lang.getObject('response.status', false, err) || 0;
					if (reqStatus == 404 && this.statusCheckResult != 'unknown') {
						// ... but existed before -> setup process is finished
						this.set('statusCheckResult', 'joined');
					}
					if (!reqStatus && !this.local_mode) {
						// request timed out as IP address has changed
						// try to make some sensible guesses concerning the current status
						this._checksTimedOut += 1;
						if (this._checksTimedOut > 20) {
							this.set('statusCheckResult', 'joined');
						}
						else if (this._checksTimedOut > 10 && this.statusCheckResult == 'cleanup-scripts') {
							this.set('statusCheckResult', 'joined');
						}
						else if (this._checksTimedOut > 10) {
							this.set('statusCheckResult', 'cleanup-scripts');
						}
					}
				}));
			});

			// once the status 'joined' has been reached, this timer can be stopped
			this.watch('statusCheckResult', lang.hitch(this, function(attr, oldVal, newVal) {
				if (newVal == 'joined') {
					this._checkStatusFileTimer.stop();
				}
			}));

			if (this.local_mode) {
				// only monitor the status file during the wizard session in a local VM
				// from the beginning on and quit the browser automatically if join has
				// been initiated from outside
				this._checkStatusFileTimer.start();
				this.watch('statusCheckResult', lang.hitch(this, function(attr, oldVal, newVal) {
					if (this._joinTriggered) {
						// join has been triggered within this session... nothing more to do
						return;
					}
					if (newVal == 'joined') {
						this.umcpCommand('setup/closebrowser').then(function (data) {
							if (!data.result) {
								window.close();
							}
						}, function (error) {
							window.close();
						});
					}
					else if (newVal != 'unknown') {
						// show progress bar
						this._progressBar.reset();
						this._progressBar.setInfo(_('Waiting for restart of server components...'), null, Infinity);
						this.standby(true, this._progressBar);
					}
				}));
			}
		},

		buildRendering: function() {
			this.inherited(arguments);
			domClass.toggle(this.domNode, 'umcInlineDialog', !this.local_mode);

			this._initStatusCheck();

			// setup the progress bar
			this._progressBar = new ProgressBar({
				umcpCommand: lang.hitch(this, 'umcpCommand')
			});
			this.own(this._progressBar);

			// start initial DHCP request... they need a reference to the progress bar
			if (this.isPageVisible('network') && this._isDHCPPreConfigured() && !this._hasPreconfiguredLinkLocalDHCPAddresses()) {
				this._initialDHCPQueriesDeferred = this._sendDHCPQueries();
			}

			this._setupCitySearch();
			this._setupJavaScriptLinks();
			this._setupNetworkDevices();
			this._setupAppGallery();
			this._setLocaleDefault();
			this._setupFooterButtons();
			this._updateOrganizationName('');
			this._evaluateBlacklist();
			this._preselectFirstVisibleRadioButton();
		},

		_randomHostName: function() {
			// generate a random 4 digit code
			var randomDigit = Math.floor(Math.random() * 9000 + 1000);
			return 'ucs-' + randomDigit;
		},

		_updateOrganizationName: function(_organization) {
			// replace umlauts, convert to lower case, replace special characters
			var organization = _organization || 'mydomain';
			organization = _replaceUmlauts(organization);
			organization = organization.toLowerCase();
			organization = organization.replace(/[^0-9a-z\-]+/g, '-').replace(/-+$/, '').replace(/^-+/, '').replace(/-+/, '-');
			if (this._isDocker()) {  // in some environments (like docker) the hostname cannot be changed
				this.getWidget('fqdn-master', '_domainname').set('value', lang.replace('{0}.intranet', [organization]));
				this.getWidget('fqdn-nonmaster-all', 'hostname').set('disabled', true);
				this.getWidget('fqdn-nonmaster-all', 'hostname').set('label', _('Hostname (unchangeable. Was set while creating the container)'));
			} else {
				var hostname = this._randomHostName();
				var fqdn = lang.replace('{0}.{1}.intranet', [hostname, organization]);
				this.getWidget('fqdn-nonmaster-all', 'hostname').set('value', hostname);
				this.getWidget('fqdn-master', '_fqdn').set('value', fqdn);
			}
		},

		_computeLDAPBase: function(domain) {
			var fqdnParts = domain.split('.');
			var ldapBaseParts = array.map(fqdnParts, function(ipart) {
				return 'dc=' + ipart;
			});
			return ldapBaseParts.join(',');
		},

		_updateLDAPBase: function(fqdn) {
			fqdn = fqdn.replace(/ /g, '');  // remove all spaces from fqdn
			var fqdnParts = fqdn.split('.').slice(1);
			var domain = fqdnParts.join('.');
			var ldapBase = this._computeLDAPBase(domain);
			var ldapBaseWidget = this.getWidget('fqdn-master', 'ldap/base');
			ldapBaseWidget.set('value', ldapBase);
		},

		_updateCityInfo: function(city) {
			var resultWidget = this.getWidget('welcome', 'result');
			if (!city || !city.id) {
				resultWidget.set('visible', false);
				resultWidget.set('content', '');
				return;
			}

			// successful match
			var nSettingsConfigured = 0;
			var cityLabel = city.label;
			if (city.country_label) {
				cityLabel += ', ' + city.country_label;
			}
			var msg = '<table class="city-match">';
			msg += _('<tr><td>City:</td><td>%s</td></tr>', cityLabel);

			var unknownStr = _('<b>Unknown</b>');
			msg += _('<tr><td>Timezone:</td><td>%s</td></tr>', city.timezone || unknownStr);
			nSettingsConfigured += !!city.timezone;

			var defaultLang = unknownStr;
			if (city.default_lang) {
				var localeWidget = this.getWidget('locale', 'locale/default');
				var locale = city.default_lang + '_' + city.country;
				array.some(localeWidget.getAllItems(), function(ilocale) {
					if (ilocale.id.indexOf(locale) === 0) {
						// found matching locale -> break loop
						city.locale = ilocale.id;
						defaultLang = ilocale.label;
						nSettingsConfigured++;
						return true;
					}
				});
			}
			msg += _('<tr><td>Default locale:</td><td>%s</td></tr>', defaultLang);

			var defaultKeyboardLabel = unknownStr;
			if (city.country) {
				var countryLowerCase = city.country.toLowerCase();
				var layoutWidget = this.getWidget('locale', 'xorg/keyboard/options/XkbLayout');
				array.some(layoutWidget.getAllItems(), function(ilayout) {
					var idxCountry = ilayout.countries.indexOf(city.country);
					if (ilayout.id == countryLowerCase || idxCountry >= 0) {
						// found matching layout -> break loop
						city.keyboard = ilayout.id;
						defaultKeyboardLabel = ilayout.label;
						nSettingsConfigured++;
						return true;
					}
				});
				if (!city.keyboard && city.default_lang) {
					// match language
					array.some(layoutWidget.getAllItems(), function(ilayout) {
						if (ilayout.language == city.default_lang) {
							// found matching layout -> break loop
							city.keyboard = ilayout.id;
							defaultKeyboardLabel = ilayout.label;
							nSettingsConfigured++;
							return true;
						}
					});
				}
			}
			msg += _('<tr><td>Keyboard layout:</td><td>%s</td></tr>', defaultKeyboardLabel);
			msg += '</table>';
			resultWidget.set('content', msg);
			resultWidget.set('visible', true);
			this._setLocaleDefault(); // set a fallback for unknown values
			this._setLocaleValues(city);

			// append button to change locale settings
			var changeSettingsButton = new Button({
				'class': 'umc-ucssetup-wizard-change-locale-button',
				label: _('Adapt settings'),
				onClick: lang.hitch(this, '_next', 'welcome-adapt-locale-settings')
			});
			resultWidget.addChild(changeSettingsButton);

			// save how many settings could be configured
			this._nLocaleSettingsConfigured = nSettingsConfigured;
		},

		_updateNetwork: function(idx, ip) {
			ip = lang.trim(ip);
			if (tools.isIPv4Address(ip)) {
				var ipParts = ip.split('.');
				var netmask = '255.255.255.0';
				var netmaskWidget = this.getWidget('network', '_netmask' + idx);
				if (!netmaskWidget.get('value')) {
					netmaskWidget.set('value', netmask);
				}

				var gatewayWidget = this.getWidget('network', 'gateway');
				if (idx === 0 && !gatewayWidget.get('value')) {
					// suggest a gateway address for the first IP address
					var gateway = ipParts.slice(0, -1).join('.') + '.1';
					gatewayWidget.set('value', gateway);
				}
			}
		},

		warnIfUidIsUsedElsewhere: function(data) {
			var values = this.getValues();
			var hostname = values['hostname'];
			var uid = hostname + '$';
			var role = values['server/role'];
			return this.uidIsUsable(uid, role).then(
				function(data) { return true; },  // callback; uid is available, just continue
				lang.hitch(this, function() {  // errback
					return this.getConfirmationToContinueWithDuplicateHostname(hostname);
				})
			);
		},

		uidIsUsable: function(uid, role) {
			var params = { uid: uid, role: role };
			lang.mixin(params, this._getCredentials());
			return this.umcpCommand('setup/check/uid', params).then(
				function(data) {
					if (data.result) { return data; }
					throw data;
				}
			);
		},

		getConfirmationToContinueWithDuplicateHostname: function(hostname) {
			return dialog.confirm(_('The hostname \'%s\' is already used for ' +
				'a computer with a different role, in the UCS domain. It is ' +
				'recommended to change the hostname for UCS to work properly.',
				hostname
			), [{
				label: _('Adjust settings'),
				name: 'adjust_settings'
			}, {
				label: _('Continue with duplicate hostname'),
				'default': true,
				name: 'continue'
			}], _('Warning')).then(
				function(choice) {
					if (choice == 'continue') { return choice; }
					throw choice;
				}
			);
		},

		_updateAppGallery: function() {
			if (!this._appGalleryUpdated) {
				this._appGalleryUpdated = true;
				this._gallery.filter(this._getAppQuery());
			}
		},

		_key2label: function(key) {
			// special handling of keys
			if (key == 'email_address') {
				return _('E-mail address to activate UCS');
			}

			// find matching widget to given key
			var widget = this.getWidget(key);
			if (widget) {
				return widget.label;
			}

			// special handling of remaining keys
			if (key.indexOf('interfaces') === 0) {
				return _('Network interfaces');
			}
			if (key == 'interfaces/primary') {
				return _('Primary network interface');
			}
			if (key == 'domainname' || key == 'hostname') {
				if (this._isRoleMaster()) {
					return _('Fully qualified domain name');
				}
				return _('Hostname');
			}
			if (key == 'components') {
				return this.getPage('software').headerText;
			}
			return null;
		},

		_updateSummaryPage: function(serverValues) {
			var guessedDomainName = serverValues.domainname;
			var _vals = this._gatherVisibleValues();
			var vals = this.getValues();
			var msg = '';

			// helper functions
			var _append = function(label, value) {
				label = arguments[0];
				value = arguments[1];
				if (value) {
					msg += '<li><i>' + label + '</i>: ' + value + '</li>';
				}
			};

			var _getItem = function(items, id) {
				var item = null;
				array.some(items, function(iitem) {
					if (iitem.id == id) {
						item = iitem;
						return true;
					}
				});
				return item;
			};

			var isFieldShown = lang.hitch(this, function(field) {
				return array.indexOf(this.disabledFields, field) < 0;
			});

			// system role
			msg += '<p><b>' + _('UCS configuration') + '</b>: ';
			var role = vals['server/role'];
			if (role == 'domaincontroller_master' && !this._isAdMember()) {
				msg += _('A new UCS domain will be created.');
			} else if (this._isUsingPreconfiguredSetup()) {
				msg += _('A preconfigured test domain will be instantiated.');
			} else if (role == 'basesystem') {
				msg += _('This system will be a base system without domain integration and without the capabilities to join one in the future.');
			} else {
				var roleLabel = {
					'domaincontroller_backup': _('DC Backup'),
					'domaincontroller_slave': _('DC Slave'),
					'memberserver': _('Member server')
				}[role];
				if (this._isAdMember()) {
					if (!this._domainHasMaster) {
						roleLabel = _('DC Master');
					}
					msg += _('This system will join an existing AD domain with the role <i>%s</i>.', roleLabel);
				} else {
					msg += _('This system will join an existing UCS domain with the role <i>%s</i>.', roleLabel);
				}
			}
			msg += '</p>';

			// localization settings
			if (isFieldShown('locale')) {
				msg += '<p><b>' + _('Localization settings') + '</b></p>';
				msg += '<ul>';
				array.forEach(['locale/default', 'timezone', 'xorg/keyboard/options/XkbLayout'], function(ikey) {
					var iwidget = this.getWidget('locale', ikey);
					var item = _getItem(iwidget.getAllItems(), vals[ikey]);
					_append(iwidget.label, item.label);
				}, this);
				msg += '</ul>';
			}

			// administrator account
			if (this._isRoleMaster()) {
				msg += '<p><b>' + _('Account information') + '</b></p>';
				msg += '<ul>';
				_append(_('Organization name'), vals.organization);
				_append(_('E-mail address to activate UCS'), vals.email_address);
				msg += '</ul>';
			}

			// network settings
			msg += '<p><b>' + _('Domain and host configuration') + '</b></p>';
			msg += '<ul>';

			var fqdn_msg = _vals._fqdn;
			if (serverValues.hostnameMessage) {
				fqdn_msg += '<br><b>' + _('Warning') + ':</b> ' + entities.encode(serverValues.hostnameMessage);
			}
			_append(_('Fully qualified domain name'), fqdn_msg);
			if (_validateHostname(vals.hostname) && guessedDomainName) {
				// if the backend gave us a guess for the domain name, show it here
				var fqdn = vals.hostname + '.' + guessedDomainName;
				_append(_('Fully qualified domain name'), fqdn);
				this._newFQDN = fqdn;
			} else {
				// 'hostname' can be host name or FQDN... choose the correct label
				var hostLabel = _validateFQDN(_vals.hostname) ? _('Fully qualified domain name') : _('Hostname');
				_append(hostLabel, _vals.hostname);
				this._newFQDN = _vals.hostname;
			}
			_append(_('LDAP base'), vals['ldap/base']);

			if (isFieldShown('network')) {
				if (_vals._dhcp) {
					_append(_('Address configuration'), _('IP address is obtained dynamically via DHCP'));
				}
				else {
					array.forEach(this._getNetworkDevices(), function(idev, i) {
						var iip = _vals['_ip' + i];
						var imask = _vals['_netmask' + i];
						if (!iip || !imask) {
							return;
						}
						_append(_('Address for %s', idev), iip + '/' + imask);
					}, this);
					_append(_('Gateway'), vals.gateway);
				}
			}

			if (isFieldShown('nameservers')) {
				var nameservers = array.filter([vals.nameserver1, vals.nameserver2], function(inameserver) {
					return inameserver;
				}).join(', ');
				_append(_('DNS server'), nameservers);
			}

			if (isFieldShown('proxy')) {
				_append(_('HTTP proxy'), vals['proxy/http']);
			}
			msg += '</ul>';

			// software components
			var apps = this._gallery.getSelectedItems();
			if (!apps.length) {
				msg += '<p><b>' + _('Software components') + '</b>: ' + _('No additional software components will be installed.') + '</p>';
			}
			else {
				msg += '<p><b>' + _('Software components') + '</b></p>';
				msg += '<ul>';
				array.forEach(apps, function(iapp) {
					msg += '<li>' + iapp.name + '</li>';
				});
			}
			msg += '</ul>';

			this.getWidget('summary', 'info').set('content', msg);
		},

		_updateValidationPage: function(details) {
			var msg = '<ul>';
			array.forEach(details, function(ientry) {
				if (ientry.valid) {
					// ignore valid entries
					return;
				}

				// prepare list item for invalid entry
				msg += '<li>';
				var label = this._key2label(ientry.key);
				if (label) {
					msg += '<b>' + label + ':</b><br/>';
				}
				msg += entities.encode(ientry.message);
				msg += '</li>';
			}, this);
			msg += '</ul>';

			// display validation information
			this.getWidget('validation', 'info').set('content', msg);
		},

		_updateErrorPage: function(details, critical) {
			var createErrorMessage = function() {
				//make the occurred errors more readable
				var previousErrorHeader = '';
				var errors = '';
				array.forEach(details, function(iDetail) {
					var splitDetail = iDetail.split(":");
					if (splitDetail.length === 2) {
						var errorHeader = splitDetail[0];
						var error = splitDetail[1];
						if (errorHeader === previousErrorHeader) {
							errors += error.trim() + '\n\n';
						} else {
							errors += "* " + errorHeader + ':\n' + error.trim() + '\n\n';
						}
						previousErrorHeader = errorHeader;
					} else {
						var readableMessage = iDetail.replace(/<br *\/?>/g, "\n");
						errors += readableMessage + '\n';
						previousErrorHeader = '';
					}
				});

				//compose an error message that is shown to the user
				var errorsBox = '<pre style="max-height: 200px">' + errors + '</pre>';
				var errorFeedbackText = _('Help us improve UCS by sending the occurred errors as feedback.');

				var errorMsg = '';
				errorMsg = '<p>' + errorMsgHeader + '</p>';
				errorMsg += errorsBox;
				errorMsg += '<p>' + errorFeedbackText + '</p>';

				return errorMsg;
			};

			var createInfoMessage = lang.hitch(this, function() {
				var infoMsg = '';
				infoMsg += '<hr>';
				infoMsg += '<p>' + _('You may restart the configuration process again with modified settings.') + '</p>';

				// TODO: all these messages about joining are useless if (critical)? ... Maybe some hint about Univention support? Or sdb article how to deal with errors.
				if (isMaster) {
					infoMsg += '<p>';
					infoMsg += _('Alternatively, you may click on the button <i>Finish</i> to exit the wizard and resolve the described problems via Univention Management Console.') + ' ';
					infoMsg += _('Failed join scripts can be executed via the UMC module <i>Domain join</i>.');
					infoMsg += '</p>';

					infoMsg += '<p>' + _('Connect to Univention Management Console on this system either as user <b>Administrator</b> or as user <b>root</b> in case the system has not yet created a new UCS domain:') + '</p>';
					infoMsg += this._getUMCLinks();
				} else if (isBaseSystem) {
					var fqdn = this._getFQDN();
					var ips = this._getIPAdresses();
					infoMsg += '<p>';
					infoMsg += _('Alternatively, you may click on the button <i>Finish</i> to exit the wizard and resolve the described problems at a later point.') + ' ';
					infoMsg += _('The system is reachable at <i>%(fqdn)s</i> or via its IP address(es) <i>%(addresses)s</i>.', {fqdn: fqdn, addresses: ips.join(', ')});
				} else { // if (isNonMaster || isAdMemberMaster || isAdMember) {
					infoMsg += '<p>';
					infoMsg += _('Alternatively, you may click on the button <i>Finish</i> to exit the wizard and resolve the described problems via Univention Management Console.') + ' ';
					infoMsg += _('Failed join scripts or a new join of the system can be executed via the UMC module <i>Domain join</i>.');
					infoMsg += '</p>';

					infoMsg += '<p>' + _('Connect to Univention Management Console on this system either as user <b>Administrator</b> or as user <b>root</b> in case the system has not yet joined the domain:') + '</p>';
					infoMsg += this._getUMCLinks();
				}

				return infoMsg;
			});

			var createFeedbackButton = lang.hitch(this, function() {
				return new Button({
					label: _('Send feedback'),
					style: 'float: right',
					onClick: lang.hitch(this, function() {
						var msg = details.join('\n');
						if (this.local_mode) {
							tools.sendTraceback(msg);
						} else {
							tools.showTracebackDialog(msg, errorMsgHeader, _('Send to vendor'));
						}
					})
				});
			});

			var displayInformation = lang.hitch(this, function() {
				var page = this.getPage('error').set('helpText', helpText);

				// display error message
				var errors = this.getWidget('error', 'errors');
				errors.destroyDescendants();

				var errorsText = new Text({
					content: createErrorMessage()
				});
				var sendFeedbackButton = createFeedbackButton();

				errors.addChild(errorsText);
				errors.addChild(sendFeedbackButton);

				// display info message
				this.getWidget('error', 'info').set('content', createInfoMessage());
			});

			var isMaster = this._isRoleMaster();
			var isBaseSystem = this._isRoleBaseSystem();
			var helpText = '<p>' + _('The system configuration could not be completed. Please choose to retry the configuration process or finish the wizard.') + '</p>';
			var errorMsgHeader = _('The following errors occurred while applying the settings.');

			displayInformation();

			// save the state
			this._criticalJoinErrorOccurred = critical;
		},

		_updateDonePage: function() {
			var isBaseSystem = this._isRoleBaseSystem();
			var isMaster = this._isRoleMaster();
			var isUniventionApp = Boolean(this.ucr['umc/web/appliance/name']);

			var fqdn = this._getFQDN();
			var ips = this._getIPAdresses();

			var msg = '';
			if (isUniventionApp) {
				msg += '<p>' + _('%s Appliance has been successfully set up.', this.ucr['umc/web/appliance/name']) + ' ';
			} else {
				msg += '<p>' + _('UCS has been successfully set up.') + ' ';
			}
			if (array.indexOf(this.disabledFields, 'reboot') !== -1) {
				msg += _('<p>Click on <i>Finish</i> to conclude the installation. The system will be prepared for the first boot procedure and will be rebooted afterwards.</p>');
			} else if (isUniventionApp) {
				msg += _('<p>Click on <i>Finish</i> for putting this system into operation.</p>');
				if (isMaster) {
					if (this.getValues().email_address) {
						msg += _('<p>When accessing the system for the first time, you will be asked to upload a new license that has been sent to your email account.</p>');
					} else {
						msg += _('<p>When accessing the system for the first time, you will be asked to request and upload a new license.</p>');
					}
				}
			} else {
				msg += _('<p>Click on <i>Finish</i> for putting UCS into operation.</p>');
			}
			this.getPage('done').set('helpText', msg);
		},

		_getUMCLinks: function() {
			var fqdn = this._getFQDN();
			var ips = this._getIPAdresses();
			var msg = '<ul>';
			array.forEach(ips, function(ip) {
				msg += lang.replace('<li>https://{0}/</li>', [ip]);
			});
			if (fqdn) {
				msg += lang.replace('<li>https://{0}/</li>', [fqdn]);
			}
			msg += '</ul>';
			return msg;
		},

		_getFQDN: function() {
			return this._newFQDN || this._gatherVisibleValues()._fqdn || this.getValues().hostname || '';
		},

		_getIPAdresses: function() {
			return array.filter(array.map(this._getNetworkDevices(), lang.hitch(this, function(idev, i) {
				return this.getWidget('network', '_ip' + i).get('value');
			})), function(ip) { return ip; });
		},

		_validateWithServer: function() {
			var vals = this.getValues();
			this.standby(true);
			return this.umcpCommand('setup/validate', { values: vals }).then(lang.hitch(this, function(response) {
				this.standby(false);
				var allValid = true;
				var result = {};
				array.forEach(response.result, function(ientry) {
					if (ientry.key && ientry.message) {
						result[`${ientry.key}Message`] = ientry.message;
					}
					if (ientry.key && ientry.value) {
						// check for values that the server returned
						result[ientry.key] = ientry.value;
					}
					else {
						allValid &= ientry.valid;
					}
				});
				if (!allValid) {
					this._updateValidationPage(response.result);
				}
				result.isValid = allValid;
				return result;
			}), lang.hitch(this, function(err) {
				this.standby(false);
				throw err;
			}));
		},

		_isRoleMaster: function() {
			var showRoleSelection = array.indexOf(this.disabledPages, 'role') === -1;
			if (!showRoleSelection) {
				return this.ucr['server/role'] == 'domaincontroller_master';
			}
			var createNewDomain = this.getWidget('_createDomain').get('value');
			return createNewDomain || this._isUsingPreconfiguredSetup();
		},

		_isRoleNonMaster: function() {
			return !this._isRoleMaster() && !this._isRoleBaseSystem() && !this._isAdMember();
		},

		_isUsingPreconfiguredSetup: function() {
			return this.getWidget('_preconfiguredDomain').get('value');
		},

		_isAdMember: function() {
			return this.getWidget('role', '_adDomain').get('value');
		},

		_isAdMemberMaster: function() {
			return this._isAdMember() && !this._domainHasMaster;
		},

		_isRoleBaseSystem: function() {
			return this.getWidget('role', '_noDomain').get('value');
		},

		_isDocker: function() {
			return !!this.ucr['docker/container/uuid'];
		},

		_isPageForRole: function(pageName) {
			if (pageName == 'software') {
				return !this._isRoleBaseSystem();
			}
			if (pageName.indexOf('-master') >= 0) {
				return this._isRoleMaster();
			}
			if (pageName.indexOf('-nonmaster-ad') >= 0) {
				return this._isRoleNonMaster() || this._isAdMember();
			}
			if (pageName.indexOf('-nonmaster-all') >= 0) {
				return !this._isRoleMaster();
			}
			if (pageName.indexOf('-nonmaster') >= 0) {
				return this._isRoleNonMaster();
			}
			if (pageName.indexOf('-ad') >= 0) {
				return this._isAdMember();
			}
			if (pageName.indexOf('-basesystem') >= 0) {
				return this._isRoleBaseSystem();
			}
			return true;
		},

		isPageVisible: function(pageName) {
			if (!this._isPageForRole(pageName)) {
				return false;
			}
			if (pageName == 'fqdn-master' && this._isUsingPreconfiguredSetup()) {
				// host and domain name are pre-configured and cannot be changed
				// in this setup
				return false;
			}
			if (pageName == 'locale' && this._nLocaleSettingsConfigured == 3) {
				// no need to display page for locale settings
				return false;
			}
			if (pageName == 'license') {
				return Boolean(this.values.license_agreement);
			}
			if (pageName == 'required_ram') {
				return Boolean(this._getMemoryWarning());
			}

			// support blacklisting of specific pages
			if (array.indexOf(this.disabledPages, pageName) > -1) {
				return false;
			}

			// default
			return true;
		},

		_hasPreconfiguredLinkLocalDHCPAddresses: function() {
			var fallbackDevices = [];
			array.forEach(this._getNetworkDevices(), function(idev) {
				var dev = this.values.interfaces[idev];
				if (!dev || !dev.ip4dynamic || !dev.ip4.length) {
					return;
				}

				var ip = dev.ip4[0][0];
				var mask = dev.ip4[0][1];
				if (_isLinkLocalDHCPAddress(ip, mask)) {
					fallbackDevices.push({
						name: idev,
						ip: ip
					});
				}
			}, this);
			return fallbackDevices.length;
		},

		areFieldsVisible: function(fieldsName) {
			return array.indexOf(this.disabledFields, fieldsName) == -1;
		},

		_getLinkLocalDHCPAddresses: function() {
			var fallbackDevices = [];
			if (this.getWidget('network', '_dhcp').get('value')){
				array.forEach(this._getNetworkDevices(), function(idev, i) {
					var ip = this.getWidget('network', '_ip' + i).get('value');
					var mask = this.getWidget('network', '_netmask' + i).get('value');
					if (_isLinkLocalDHCPAddress(ip, mask)) {
						fallbackDevices.push({
							name: idev,
							ip: ip
						});
					}
				}, this);
			}
			return fallbackDevices;
		},

		_validatePage: function(pageName) {
			if (pageName == 'software') {
				// validate software components
				var packages = {};
				array.forEach(this._gallery.getSelectedItems(), function(iapp) {
					var ipackages = [].concat(iapp.default_packages, iapp.default_packages_master);
					array.forEach(ipackages, function(ipackage) {
						packages[ipackage] = true;
					});
				});
				if (packages['univention-samba'] && packages['univention-samba4']) {
					_alert(_('It is not possible to install Samba 3 and Samba 4 on one system. Please select only one of these components.'));
					return false;
				}
				if (packages['univention-virtual-machine-manager-node-kvm'] && packages['univention-virtual-machine-manager-node-xen']) {
					_alert(_('It is not possible to install KVM and XEN components on one system. Please select only one of these components.'));
					return false;
				}
			}

			var page = this.getPage(pageName);
			if (!page || !page._form) {
				return true;
			}
			var invalidWidgets = page._form.getInvalidWidgets();
			if (invalidWidgets.length !== 0) {
				// focus the first invalid widget
				array.some(invalidWidgets, function(ikey) {
					var iwidget = this.getWidget(pageName, ikey);
					if (iwidget.focus) {
						iwidget.focus();
						return true;
					}
				}, this);
				return false;
			}

			// password length check
			if (pageName == 'credentials-master' || pageName == 'fqdn-nonmaster-all') {
				var passwordWidget = this.getWidget(pageName, 'root_password');
				var password = passwordWidget.get('value');
				if (passwordWidget.get('visible') && password && password.length < 8) {
					passwordWidget.focus();
					_alert(_('The root password is too short. For security reasons, your password must contain at least 8 characters.'));
					return false;
				}
			}

			if (pageName === 'schooldomain-slave') {
				var hasEduSchoolRole = lang.hitch(this, function() {
					return array.some(this._serverSchoolRoles, function(role) {
						return role.startsWith('dc_slave_edu:school:');
					});
				});
				var hasAdminSchoolRole = lang.hitch(this, function() {
					return array.some(this._serverSchoolRoles, function(role) {
						return role.startsWith('dc_slave_admin:school:');
					});
				});
				if (this._getRole() === 'domaincontroller_slave' && this._isSchoolMultiServerDomain) {
					var _vals = this._gatherVisibleValues();
					var hasAdminAlert = function() {
						_alert(_('For this system, a computer object already exists in the LDAP directory that has been configured for the role &quot;<i>school server in the administration network</i>&quot; and thus contradicts your selection. Please check and correct this before proceeding.'));
					};
					var hasEduAlert = function() {
						_alert(_('For this system, a computer object already exists in the LDAP directory that was configured for the role &quot;<i>school server in the educational network</i>&quot; and thus contradicts your selection. Please check and correct this before proceeding.'));
					};
					var missingEduAlert = function() {
						_alert(_('If this system is to become a school server in the educational network, please first check whether a corresponding school exists and whether the computer name of this system was specified as the <i>school server for the educational network</i>.'));
					};
					var missingAdminAlert = function() {
						_alert(_('If this system is to become a school server in the administration network, please first check whether a corresponding school exists and whether the computer name of this system has been specified as the <i>school server for the administration network</i>.'));
					};


					if (_vals._schoolRoleEducational) {
						if (hasEduSchoolRole()) {
							return true;
						} else if (hasAdminSchoolRole()) {
							hasAdminAlert();
							return false;
						} else {
							missingEduAlert();
							return false;
						}
					} else if (_vals._schoolRoleAdministrative) {
						if (hasAdminSchoolRole()) {
							return true;
						} else if (hasEduSchoolRole()) {
							hasEduAlert();
							return false;
						} else {
							missingAdminAlert();
							return false;
						}
					} else {
						if (hasEduSchoolRole()) {
							hasEduAlert();
							return false;
						} else if (hasAdminSchoolRole()) {
							hasAdminAlert();
							return false;
						} else {
							return true;
						}
					}
				}
			}

			// check network device configuration
			if (pageName == 'network' && this.getWidget('network', '_ip0').get('visible')) {
				var _vals = this._pages.network._form.get('value');
				var nConfiguredInterfaces = 0;
				for (var idx = 0; idx < 4; ++idx) {
					nConfiguredInterfaces += Boolean(_vals['_ip' + idx] && _vals['_netmask' + idx]);
				}
				if (!nConfiguredInterfaces && !_vals._dhcp) {
					this.getWidget('network', '_ip0').focus();
					_alert(_('At least one network device needs to be properly configured.'));
					return false;
				}
			}
			return true;
		},

		join: function() {
			// initialize and show the progress bar
			this._progressBar.reset();
			this._progressBar.setInfo(_('Initialize the configuration process ...'), null, Infinity);
			this.standby(true, this._progressBar);

			topic.publish('/umc/actions', this.moduleID, 'configure', 'start');

			// function to save data
			var _join = lang.hitch(this, function(values, dcname, username, password) {
				// make sure that no re-login is tried/required due to the server time
				// being adjusted in 40_ssl/10ssl (cf., Bug #38455)
				// and make sure no page reload is requested
				tools.checkSession(false);
				tools.status('ignorePageReload', true);

				// join system
				var joinDeferred = null;
				if (this._isUsingPreconfiguredSetup()) {
					// in the pre-configured setup, we do not need a real join process,
					// only the standard setup save command which triggers the setup scripts
					joinDeferred = this.umcpCommand('setup/save', {
						values: values,
						run_hooks: true
					}, false);
				}
				else {
					joinDeferred = this.umcpCommand('setup/join', {
						values: values,
						// make sure that the username/password are null and not undefined
						// ... server cannot handle "undefined"
						dcname: dcname || null,
						username: username || null,
						password: password || null,
					}, false);
				}

				// we need to fetch progress information manually in order to be able to
				// react on timeouts due to IP address changes (detected by the status check)
				var deferred = new Deferred();
				var _pollProgressInfo = lang.hitch(this, function() {
					var _areSetupScriptsRunning = lang.hitch(this, function(value) {
						return value == 'setup-scripts' || value == 'unknown';
					});
					if (!_areSetupScriptsRunning(this.statusCheckResult)) {
						// stop polling as setup scripts have been passed and
						// clean up scripts/appliance hooks are running now
						deferred.resolve();
						return;
					}
					var _schedulePoll = function() {
						tools.defer(_pollProgressInfo, 500);
					};

					// in case the join process is about to finish, cancel the command
					var requestDeferred = null;
					var watchHandler = this.watch('statusCheckResult', function(attr, oldVal, newVal) {
						if (!_areSetupScriptsRunning(newVal)) {
							watchHandler.remove();
							if (!requestDeferred.isFulfilled()) {
								requestDeferred.cancel();
							}
						}
					});

					// query finished request
					requestDeferred = this.umcpCommand('setup/finished', {}, false).then(lang.hitch(this, function(response) {
						var result = response.result;
						if (!result) {
							// not finished yet... retry again
							_schedulePoll();
						} else {
							this._progressBar.setInfo(result.component, result.info, result.steps, result.errors, result.critical);
							if (result.finished) {
								// finished :)
								deferred.resolve();
							} else {
								// not finished yet...
								_schedulePoll();
							}
						}
					}), _schedulePoll);

				});

				joinDeferred.then(lang.hitch(this, function() {
					// make sure the server process cannot die
					this.umcpCommand('setup/ping', {keep_alive: true}, false);

					// start polling for progress information
					// (force value 0 to avoid an animated progress bar from right to left)
					this._progressBar._progressBar.set('value', 0);
					_pollProgressInfo();
				}), lang.hitch(this, function(error) {
					this._progressBar.setInfo(undefined, undefined, undefined, [tools.parseError(error).message], true);
					deferred.resolve();
				}));

				return deferred;
			});

			var _checkJoinSuccessful = lang.hitch(this, function() {
				var errors = this._progressBar.getErrors();
				if (errors.errors.length) {
					this._updateErrorPage(errors.errors, errors.critical);
					this._checkStatusFileTimer.stop();
					this.set('statusCheckResult', 'error');
					throw new Error('Join process failed!');
				}
				else {
					this._updateDonePage();
				}
			});

			var _waitForCleanup = lang.hitch(this, function(joinSuccessful) {
				// monitor join process via status file
				var deferred = new Deferred();
				this.watch('statusCheckResult', lang.hitch(this, function(attr, oldVal, newVal) {
					if (newVal == 'joined' || newVal == 'error') {
						deferred.resolve();
						topic.publish('/umc/actions', this.moduleID, 'configure', newVal);
					}
					else if (newVal != 'unknown' && newVal != 'setup-scripts') {
						// setup process passed setup-scripts -> update the progress bar
						this._progressBar.setInfo(_('Waiting for restart of server components...'), null, Infinity);
					}
				}));

				// start timer for status check
				this._checkStatusFileTimer.setInterval(2000);
				if (!this._checkStatusFileTimer.isRunning) {
					this._checkStatusFileTimer.start();
				}

				return deferred;
			});

			// chain all methods together
			var joinDeferred = null;
			var values = this.getValues();
			var role = values['server/role'];
			if (role == 'domaincontroller_master' || role == 'basesystem') {
				joinDeferred = _join(values);
			} else {
				// for any other role, we need domain admin credentials
				var credentials = this._getCredentials();
				joinDeferred = _join(values, credentials.ad ? null : credentials.address, credentials.username, credentials.password);
			}
			joinDeferred = joinDeferred.then(_checkJoinSuccessful);

			// We have two sources of information:
			// (a) progress information via the setup/finished
			// (b) setup status information via /ucs_setup_process_status.json
			// In case the network interface has been changed, (a) will fail at
			// a certain point, and (b) will be able to provide additional extra
			// information to recover from this case.
			return all({
				cleanup: _waitForCleanup(),
				join: joinDeferred
			}).then(lang.hitch(this, function() {
				this.standby(false);
				return true;
			}), lang.hitch(this, function() {
				this.standby(false);
				return false;
			}));
		},

		_forcePageTemporarily: function(pageName) {
			// if it was hidden but now is forced to be shown, whitelist it
			// for the future with back/next buttons (as well as add its values in getValues())
			this.disabledPages = array.filter(this.disabledPages, function(disabledPage) {
				return disabledPage != pageName;
			});
			this._forcedPage = pageName;
			tools.defer(lang.hitch(this, function() {
				// reset the _forcedPage variable to allow a page change again
				this._forcedPage = null;
			}), 500);
			return pageName;
		},

		_wantsToJoin: function() {
			if (this._isRoleBaseSystem()) {
				return false;
			}
			if (this._isRoleNonMaster()) {
				var vals = this.getValues();
				return vals['start/join'];
			}
			return true;
		},

		_getRoleForDomainChecks: function(evalStartJoin) {
			var vals = this.getValues();
			var role = 'master';
			if (this._isAdMember()) {
				role = 'ad';
			} else if (this._isRoleNonMaster()) {
				role = 'nonmaster';
				if (evalStartJoin) {
					if (!vals['start/join']) {
						role = 'none';
					}
				}
			} else if (this._isRoleBaseSystem()) {
				role = 'basesystem';
			}
			return role;
		},

		_checkDomain: function() {
			var nameserver = this.getWidget('network', 'nameserver1').get('value');
			return this.standbyDuring(this.umcpCommand('setup/check/domain', {role: this._getRoleForDomainChecks(false), nameserver: nameserver}, false).then(function(data) {
				return data.result;
			}));
		},

		_checkDomainJoinInformation: function() {
			var params = {
				domain_check_role: this._getRoleForDomainChecks(true),
				role: this.getValues()['server/role']
			};
			lang.mixin(params, this._getCredentials());
			return this.umcpCommand('setup/check/join_info', params).then(function(data) {
				return data.result;
			});
		},

		_checkSchoolInformation: function() {
			var params = {
				hostname: this.getWidget('fqdn-nonmaster-all', 'hostname').get('value'),
			};
			lang.mixin(params, this._getCredentials());
			return this.umcpCommand('setup/check/school_info', params).then(function(data) {
				return data.result;
			});
		},

		_domainHasActivatedLicense: function () {
			var credentials = this._getCredentials();
			return this.umcpCommand('setup/check/license', credentials).then(function(data) {
				return data.result;
			});
		},

		_getCredentials: function() {
			var address, username, password, dns;
			var isAdMember = this._isAdMember();
			if (isAdMember) {
				dns = !this._domainReplaceMaster;
				address = this.getWidget('credentials-ad', 'ad/address').get('value');
				username = this.getWidget('credentials-ad', 'ad/username').get('value');
				password = this.getWidget('credentials-ad', 'ad/password').get('value');
			} else {
				dns = this.getWidget('credentials-nonmaster', '_ucs_autosearch_master').get('value');
				address = this.getWidget('credentials-nonmaster', '_ucs_address').get('value');
				username = this.getWidget('credentials-nonmaster', '_ucs_user').get('value');
				password = this.getWidget('credentials-nonmaster', '_ucs_password').get('value');
			}
			return {
				ad: isAdMember,
				dns: dns,
				nameserver: this.getWidget('network', 'nameserver1').get('value'),
				address: address,
				username: username,
				password: password
			};
		},

		_updateButtons: function(pageName) {
			this.inherited(arguments);
			var buttons = this._pages[pageName]._footerButtons;
			if (pageName == 'validation') {
				domClass.add(buttons.next.domNode, 'dijitDisplayNone');
				domClass.add(buttons.previous.domNode, 'umcSubmitButton');
			}
		},

		next: function(pageName) {
			// disallow page changing more than every 500 milliseconds (Bug #27734)
			if (this._forcedPage) {
				return this._forcedPage;
			}
			topic.publish('/umc/actions', this.moduleID, 'wizard', pageName, 'next');

			// in case system/setup/boot/start == false go directly to the
			// last page as system-setup-boot has been removed/disabled
			// ... this avoids problems when page reloading (or a relogin)
			// at the end of the wizard
			if (tools.isFalse(this.ucr['system/setup/boot/start'])) {
				this._updateDonePage();
				return this._forcePageTemporarily('done');
			}

			// validation of form fields
			if (!this._validatePage(pageName)) {
				return this._forcePageTemporarily(pageName);
			}

			var nextPage = this.inherited(arguments);

			if (nextPage == 'network' && this._initialDHCPQueriesDeferred) {
				// process the initial dhcp queries
				this._processDHCPQueries(this._initialDHCPQueriesDeferred);
			}

			// dummy Deferred
			var deferred = new Deferred();
			deferred.resolve(nextPage);

			// check dhcp config
			if (pageName == 'network') {
				var _throwErrorIfNextWasCanceled = lang.hitch(this, function(selectedNextPage){
					if (selectedNextPage == pageName)
						throw selectedNextPage;
					return selectedNextPage;
				});

				var _getConfirmationToContinueWithLinkLocalAdresses = lang.hitch(this, function(fallbackDevices) {
					var devicesStr = array.map(fallbackDevices, function(idev) {
						return lang.replace('<li><b>{name}:</b> {ip}</li>', idev);
					}).join('\n');
					var msg = _('<p>One or more network interfaces could not obtain an IP address via DHCP. ' +
						'These interfaces will use automatic generated private addresses instead (APIPA).</p> ' +
						'<ul> %s </ul> <p>Please adjust your DHCP settings or confirm use of private address(es).</p>',
						devicesStr
					);
					var buttonLabel = _('Continue with 169.254.*.* addresse(s)');
					var allDevices = this._getNetworkDevices();
					if (fallbackDevices.length === allDevices.length) {
						msg = _('<p>With the current settings <b> no </b> internet access is available.</p>' +
							'<p>Because of this some functions like the App Center or software-updates will not be accessible</p>'
						) + msg;
						buttonLabel = _('Continue without internet access');
					}
					return dialog.confirm(msg, [{
						label: _('Cancel'),
						name: pageName
					}, {
						label: buttonLabel,
						'default': true,
						name: nextPage
					}], _('Warning')).then(
						_throwErrorIfNextWasCanceled
					);
				});

				var _getConfirmationToContinueWithoutGateway = lang.hitch(this, function(selectedNextPage) {
					return dialog.confirm(_('No gateway has been specified and thus no access to the internet is ' +
						'possible. As UCS requires internet access for its functionality, certain services (e.g., ' +
						'software updates, installation of further software components) will not be able to operate as expected.'
					), [{
						label: _('Adjust settings'),
						name: pageName
					}, {
						label: _('Continue without internet access'),
						'default': true,
						name: nextPage
					}], _('Warning')).then(
						_throwErrorIfNextWasCanceled
					);
				});

				var _getConfirmationToContinueWithoutRepositoryAccess = lang.hitch(this, function(selectedNextPage) {
					// FIXME: It's ugly that this function is used here, but I couldn't find a way to do without.
					_throwErrorIfNextWasCanceled(selectedNextPage);

					return dialog.confirm(
						_.ngettext(
							'The server <b>%s</b> cannot be reached. For UCS to work properly, please ' +
							'configure the network, any proxy and firewall to allow UCS to access this server.',
							'These servers cannot be reached: <ul><li>%s</li></ul>' +
							'For UCS to work properly, please configure the network, any proxy and firewall to ' +
							'allow UCS to access these servers.',
							unreachableServers.length,
							unreachableServers.join('</li><li>')
						),
						[{
							label: _('Adjust settings'),
							name: pageName
						},
						{
							label: _('Continue without access to the repository servers'),
							'default': true,
							name: nextPage
						}],
						_('Warning')
					).then(
						_throwErrorIfNextWasCanceled
					);
				});

				var _applyNetworkSettings = lang.hitch(this, function(selectedNextPage) {
					// need network settings to be applied?
					var networkValues = this.getPage('network')._form.get('value');
					var haveValuesChanged = !tools.isEqual(networkValues, this._lastAppliedNetworkValues);
					if (!haveValuesChanged) {
						return selectedNextPage;
					}
					this._lastAppliedNetworkValues = networkValues;

					// apply network settings
					var values = this.getValues();
					this.umcpCommand('setup/net/apply', {
						values: values,
						demo_mode: this._isUsingPreconfiguredSetup()
					}, false);

					// wait a moment and then check the status
					var requestDeferred = tools.defer(lang.hitch(this, function() {
						// query state of applying the network settings
						return this.umcpCommand('setup/net/apply_check_finished', {}, false, null, {
							xhrTimeout: 5,
							maxTimeoutRetry: 5,
							messageInterval: 400
						});
					}), 2000).then(function() {
						return selectedNextPage;
					});

					this.standbyDuring(requestDeferred);
					return requestDeferred;
				});

				var _returnCurrentPage = lang.hitch(this, function(selectedNextPage) {
					return pageName;
				});

				var unreachableServers;

				var checkIfRepositoriesAreReachable = lang.hitch(this, function(selectedNextPage) {
					return this.umcpCommand('setup/check/repository_accessibility').then(
						function(data) {
							if(data.result.length === 0)
								return selectedNextPage;
							unreachableServers = data.result;
							throw selectedNextPage;
						}
					);
				});

				var fallbackDevices = this._getLinkLocalDHCPAddresses();
				if (fallbackDevices.length) {
					deferred = _getConfirmationToContinueWithLinkLocalAdresses(fallbackDevices);
				}

				var gateway = this.getWidget('network', 'gateway').get('value');
				if (!gateway) {
					deferred = deferred.then(_getConfirmationToContinueWithoutGateway);
				}

				deferred = deferred.then(
					_applyNetworkSettings,  // callback
					_returnCurrentPage  // errback; some previous dialog was canceled
				);

				deferred = deferred.then(
					_throwErrorIfNextWasCanceled  // This is to prevent unnecessary calls of checkIfRepositoriesAreReachable().
				);
				deferred = deferred.then(
					checkIfRepositoriesAreReachable
				).then(
					function(selectedNextPage) { return selectedNextPage; },  // callback; just continue
					_getConfirmationToContinueWithoutRepositoryAccess  // errback
				);

				deferred = deferred.then(
					function(selectedNextPage) { return selectedNextPage; },  // callback; just continue
					_returnCurrentPage  // errback; some previous dialog was canceled
				);

				// apply network settings
				if (this.isPageVisible('role')) {
					return this.standbyDuring(deferred);
				}
			}

			if (pageName == 'role' || (pageName == 'network' && !this.isPageVisible('role'))) {
				if (this._isRoleMaster() || this._isRoleBaseSystem()) {
					// no further checks regarding the domain need to done
					return this._forcePageTemporarily(nextPage);
				}

				var nextPageIfNoAdMember = 'role-nonmaster-ad';
				if (!this.isPageVisible('role')) {
					nextPageIfNoAdMember = 'credentials-nonmaster';
				}
				var _noUcsDomainWarning = lang.hitch(this, function() {
					this.getWidget('credentials-nonmaster', '_ucs_autosearch_master').set('value', false);
					return dialog.confirm(_('No domain controller was found at the address of the name server. It is recommended to verify that the network settings are correct.'), [{
						label: _('Adjust settings'),
						name: 'network'
					}, {
						label: _('Continue with incomplete settings'),
						'default': true,
						name: nextPageIfNoAdMember
					}], _('Warning')).then(lang.hitch(this, function(response) {
						return this._forcePageTemporarily(response);
					}));
				});

				var _adJoinWithUnreachableMaster = lang.hitch(this, function(infos) {
					this._domainReplaceMaster = false;
					return dialog.confirm(_('A previous UCS system has already joined into the Active Directory domain. Please make sure the system "%(ucs_master_fqdn)s" is reachable via SSH. If you continue with "Replace system" the registration of the previous UCS system will be removed.', infos), [{
						label: _('Cancel'),
						name: pageName
					}, {
						label: _('Replace system'),
						name: 'credentials-ad'
					}], _('Warning')).then(lang.hitch(this, function(response) {
						var forcedPage = this._forcePageTemporarily(response);
						if (response == 'credentials-ad') {
							this._domainHasMaster = false;
							this._domainReplaceMaster = true;
							return forcedPage;
						}
						return forcedPage;
					}));
				});

				var _noAdDcFoundWarning = lang.hitch(this, function() {
					dialog.alert(_('No domain controller was found at the address of the name server. Please adjust your network settings.'));
					return this._forcePageTemporarily('network');
				});

				var _adJoinWithNonMasterNotPossibleWarning = lang.hitch(this, function() {
					dialog.alert(_('It seems that a UCS DC master system has already joined into the Windows AD domain. Please choose a different option as other system roles for joining an AD domain are not available.'));
					return pageName;
				});

				return deferred.then(lang.hitch(this, function() {
					return this._checkDomain().then(lang.hitch(this, function(info) {
						if (this._isAdMember()) {
							this._domainHasMaster = info.ucs_master;
							if (!info.dc_name) {
								return _noAdDcFoundWarning();
							}
							this.getWidget('credentials-ad', 'ad/address').set('value', info.dc_name);
							if (info.ucs_master) {
								// UCS DC master already has joined into the AD domain
								if (!info.ucs_master_reachable) {
									// The DC Master is not reachable via SSH.
									// This might be the case if the system was thrown away.
									// Let the user choose:
									// - Either retry the connection or
									// - configure this system as DC Master and replace the old DC Master entry in the DNS of the AD server
									return _adJoinWithUnreachableMaster(info);
								}
								// let the user choose a system role
								if (this._areRolesDisabled('domaincontroller_backup', 'domaincontroller_slave', 'memberserver')) {
									return _adJoinWithNonMasterNotPossibleWarning();
								}
								return this._forcePageTemporarily('role-nonmaster-ad');
							}
							return this._forcePageTemporarily('credentials-ad');
						}
						else {
							if (info.ucs_master) {
								this.getWidget('credentials-nonmaster', '_ucs_autosearch_master').set('value', true);
								this.getWidget('credentials-nonmaster', '_ucs_address').set('value', info.dc_name || '');
								return this._forcePageTemporarily(nextPageIfNoAdMember);
							}
							return _noUcsDomainWarning();
						}
					}), lang.hitch(this, function() {
						if (this._isAdMember()) {
							return _noAdDcFoundWarning();
						}
						return _noUcsDomainWarning();
					}));
				}));
			}

			if (pageName == 'credentials-ad' || pageName == 'credentials-nonmaster') {
				var acceptCredentials = function(result) {
					this._domainName = result.domain;
					this._install_memberof_overlay = result.install_memberof_overlay;
				};

				var setNextPageToSamePage = function() {
					nextPage = pageName;
					return nextPage;
				};

				var resetCredentialPageAndContinue = function() {
					if (nextPage == 'credentials-nonmaster') {
						this.getWidget('credentials-nonmaster', '_ucs_password').reset();
					} else if (nextPage == 'credentials-ad') {
						this.getWidget('credentials-ad', 'ad/password').reset();
					}
					return this._forcePageTemporarily(nextPage);
				};

				var promise = this.standbyDuring(
					this._checkDomainJoinInformation().then(
						lang.hitch(this, acceptCredentials),  // callback
						lang.hitch(this, setNextPageToSamePage)  // errback
					).then(
						lang.hitch(this, resetCredentialPageAndContinue)  // callback; will always be called
					)
				);
				return promise;
			}

			if (nextPage == 'software') {
				this._updateAppGallery();
			}

			// evaluate blacklist after update of view
			this._evaluateBlacklist();

			// extra handling for specific pages
			if (pageName == 'welcome-adapt-locale-settings') {
				return this._forcePageTemporarily('locale');
			}

			var _validationFunction = lang.hitch(this, function() {
				return this._validateWithServer().then(lang.hitch(this, function(response) {
					// jump to summary page if everything is fine...
					// else display validation errors
					if (response.isValid) {
						this._updateSummaryPage(response);
						return 'summary';
					}
					return 'validation';
				}), function() {
					// fallback -> the error will be displayed anyways...
					// stay on the current page
					return pageName;
				});
			});
			var shouldShowSchooldomainSlavePage = lang.hitch(this, function() {
				return (pageName === 'fqdn-nonmaster-all' && this._getRole() === 'domaincontroller_slave');
			});
			if ((nextPage === 'schooldomain-slave') && ! shouldShowSchooldomainSlavePage()) {
				nextPage = this.next(nextPage);
			}

			if (pageName == 'fqdn-master' || pageName == 'fqdn-nonmaster-all') {
				var deferred = new Deferred();
				deferred.resolve(nextPage);

				var hostname = this.getValues().hostname || '';
				if (hostname.length > 13) {
					var applianceName = _('the UCS system');
					if (this.ucr['umc/web/appliance/name']) {
						applianceName = _('the %s Appliance', this.ucr['umc/web/appliance/name']);
					}
					var msg = _('<p>The hostname <i>%s</i> is longer than 13 characters.</p><p>It will not be possible to install an Active Directory compatible Domaincontroller (Samba 4) or UCS@school. The hostname cannot be changed after the installation of %s. It is recommended to shorten the hostname to maximal 13 characters.</p>', hostname, applianceName);
					deferred = deferred.then(function(selectedNextPage) {
						return dialog.confirm(msg, [{
							label: _('Adjust hostname'),
							name: pageName
						}, {
							label: _('Continue'),
							name: nextPage,
							default: true
						}], _('Warning')).then(function(selectedNextPage) {
							if (selectedNextPage == pageName)
								throw selectedNextPage;
							return selectedNextPage;
						});
					});
				}

				// confirm empty passwords (if not required)
				if (pageName == 'credentials-master' || pageName == 'fqdn-nonmaster-all') {
					var passwordWidget = this.getWidget(pageName, 'root_password');
					var password = passwordWidget.get('value');


					if (passwordWidget.get('visible') && !password) {
						deferred = deferred.then(function(selectedNextPage) {
							// callback; will always be used
							return dialog.confirm(_('Root password empty. Continue?'), [{
								label: _('Cancel'),
								name: pageName
							}, {
								label: _('Continue'),
								'default': true,
								name: nextPage
							}], _('Warning')).then(function(selectedNextPage) {
								if (selectedNextPage == pageName)
									throw selectedNextPage;
								return selectedNextPage;
							});
						});
					}

					if (pageName === 'fqdn-nonmaster-all') {
						deferred = deferred.then(lang.hitch(this, function(selectedNextPage) {
							// callback; will only be called, if previous dialog was not canceled
							if (this._isRoleNonMaster() && this._wantsToJoin()) {
								lang.hitch(this, this.warnIfUidIsUsedElsewhere)
							}
							if (nextPage === 'schooldomain-slave') {
								return this._checkSchoolInformation().then(lang.hitch(this, function(result) {
									this._serverSchoolRoles = result.server_school_roles;
									this._isSchoolMultiServerDomain = result.is_school_multiserver_domain;
								})).then(lang.hitch(this, function() {
									if (! this._isSchoolMultiServerDomain) {
										 nextPage = this.next(nextPage);
									}
								}));
							}
						}));
					}
				}

				deferred = deferred.then(lang.hitch(this, function(selectedNextPage) {
						// callback
						if (selectedNextPage == 'validation') {
							return _validationFunction();
						}
						return this._forcePageTemporarily(nextPage);
					}),
					lang.hitch(this, function(selectedNextPage) {
						return this._forcePageTemporarily(pageName);  // errback; page change was canceled
					})
				);

				var promise = this.standbyDuring(deferred);
				return promise;
			} 


			// update summary page
			if (nextPage == 'validation') {
				return _validationFunction();
			}
			if (pageName == 'summary') {
				this._joinTriggered = true;
				return this.join().then(lang.hitch(this, function(success) {
					return success ? 'done' : 'error';
				}));
			}
			return this._forcePageTemporarily(nextPage);
		},

		previous: function(pageName) {
			// disallow page changing more than every 500 milliseconds (Bug #27734)
			if (this._forcedPage) {
				return this._forcedPage;
			}
			topic.publish('/umc/actions', this.moduleID, 'wizard', pageName, 'previous');

			var previousPage = this.inherited(arguments);

			if (previousPage == 'role' || (previousPage == 'network' && !this.isPageVisible('role'))) {
				// reset the temporary variable if user navigates back in wizard
				this._domainHasMaster = null;
			}

			if (previousPage == 'warning-basesystem') {
				previousPage = this.previous(previousPage);
			}

			if (pageName == 'credentials-ad') {
				if (this._domainHasMaster) {
					previousPage = 'role-nonmaster-ad';
				} else {
					previousPage = 'role';
				}
			}
			if (previousPage === 'schooldomain-slave') {
				if ( this._getRole() !== 'domaincontroller_slave' || ! this._isSchoolMultiServerDomain) {
					return this.previous(previousPage);
				}
			}

			if (pageName == 'error' || pageName == 'summary') {
				previousPage = this.isPageVisible('software') ? 'software' : 'network';
			}
			return this._forcePageTemporarily(previousPage);
		},

		canCancel: function() {
			return false;
		},

		hasNext: function(pageName) {
			var result = this.inherited(arguments);
			if (pageName == 'error') {
				return false;
			}
			return result;
		},

		hasPrevious: function(pageName) {
			var result = this.inherited(arguments);
			if (pageName == 'done') {
				return false;
			}
			return result;
		},

		onReload: function(newLocale) {
			// event stub
		},

		_gatherVisibleValues: function() {
			// collect values from visible pages and visible widgets
			var _vals = {};
			array.forEach(this.pages, function(ipageConf) {
				if (this.isPageVisible(ipageConf.name) || ipageConf.name == 'locale') {
					var ipage = this.getPage(ipageConf.name);
					if (!ipage || !ipage._form) {
						return;
					}
					tools.forIn(ipage._form._widgets, function(iname, iwidget) {
						var val = iwidget.get('value');
						if (iwidget.get('visible') && val !== undefined) {
							_vals[iname] = iwidget.get('value');
						}
					});
				}
			}, this);

			// put docker widgets together
			if (_vals._hostname && _vals._domainname) {
				_vals._fqdn = _vals._hostname + '.' + _vals._domainname;
			}
			return _vals;
		},

		_getRole: function() {
			var _vals = this._gatherVisibleValues();
			var showRoleSelection = array.indexOf(this.disabledPages, 'role') === -1;
			var implicitMaster = this._isAdMemberMaster() || _vals._preconfiguredDomain;
			if (!showRoleSelection) {
				return this.ucr['server/role'];
			} else if (_vals._createDomain || implicitMaster) {
				return 'domaincontroller_master';
			} else if (_vals._roleBackup) {
				return 'domaincontroller_backup';
			} else if (_vals._roleSlave) {
				return 'domaincontroller_slave';
			} else if (_vals._roleMember) {
				return 'memberserver';
			} else if (_vals._noDomain) {
				return 'basesystem';
			}
		},

		getValues: function() {
			// network configuration
			var _vals = this._gatherVisibleValues();
			var vals = {};
			if (this.isPageVisible('network') && this.areFieldsVisible('network')) {
				// prepare values for network interfaces
				vals.interfaces = {};
				array.forEach(this._getNetworkDevices(), function(idev, i) {
					// prepare interface entry
					var iconf = {
						name: idev,
						interfaceType: 'Ethernet',
						ip4dynamic: _vals._dhcp
					};

					// if IPs are not given for a static configuration -> ignore interface
					var iip = _vals['_ip' + i];
					var imask = _vals['_netmask' + i];
					var ipIsSet = iip && imask;
					if (!_vals._dhcp && !ipIsSet) {
						return;
					}

					// set primary interface
					if (!('interfaces/primary' in vals)) {
						vals['interfaces/primary'] = idev;
					}

					// set IP address and mask
					iconf.ip4 = [];
					iconf.ip6 = [];
					if (ipIsSet && tools.isIPv4Address(iip)) {
						// IPv4 address
						iconf.ip4 = [[iip, imask]];
					}
					else if (ipIsSet && tools.isIPv6Address(iip)) {
						// IPv6 address
						iconf.ip6 = [[iip, imask, 'default']];
					}
					vals.interfaces[idev] = iconf;
				});
			}

			// handle ipv6 gateway
			if (tools.isIPv6Address(_vals.gateway)) {
				_vals['ipv6/gateway'] = _vals.gateway;
				_vals.gateway = '';
			}

			// domain name handling
			if (_vals.hostname && _validateFQDN(_vals.hostname)) {
				// FQDN is specified instead of hostname
				_vals._fqdn = _vals.hostname;
			}
			if (_vals._fqdn) {
				// FQDN is specified
				// -> split FQDN into hostname and domain name
				var parts = _vals._fqdn.split('.');
				_vals.hostname = parts.shift();
				_vals.domainname = parts.join('.');
			}

			// server role handling
			vals['server/role'] = this._getRole();

			// software components
			var packages = [];
			array.forEach(this._gallery.getSelectedItems(), function(iapp) {
				packages = packages.concat(iapp.default_packages, iapp.default_packages_master);
			});
			vals.components = packages;

			// prepare the dictionary with final values
			tools.forIn(_vals, function(ikey, ival) {
				if (typeof ikey == "string" && ikey.indexOf('_') !== 0 && (ival || ival === false)) {
					// ignore values starting with '_'
					vals[ikey] = ival;
				}
			});
			vals['ad/member'] = this._isAdMember();
			if (this._isAdMember() || this._isRoleNonMaster()) {
				vals.nameserver1 = this.getWidget('network', 'nameserver1').get('value');
				if (this._domainName) {
					vals.domainname = this._domainName;
					if (this._isAdMemberMaster()) {
						vals['ldap/base'] = this._computeLDAPBase(this._domainName);
					}
				}
			}
			if (this._isUsingPreconfiguredSetup()) {
				// explicitly register specified nameserver as forwarder in pre-configured setup
				// (usually this is done by the join scripts when setting up a DC master)
				vals.nameserver1 = _vals._ip0;
				delete vals.nameserver2;
				vals['dns/forwarder1'] = _vals.nameserver1;
				vals['dns/forwarder2'] = _vals.nameserver2;
			}

			// memberof overlay
			vals.install_memberof_overlay = this._install_memberof_overlay;

			return vals;
		},

		destroy: function() {
			if (this._checkStatusFileTimer.isRunning) {
				this._checkStatusFileTimer.stop();
			}
			this.inherited(arguments);
		}
	});
});
