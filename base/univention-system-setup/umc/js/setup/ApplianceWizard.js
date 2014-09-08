/*
 * Copyright 2014 Univention GmbH
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
/*global define require console*/

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
	"dijit/form/Select",
	"dijit/Tooltip",
	"dijit/focus",
	"dojox/html/styles",
	"dojox/timing/_base",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/TextBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/widgets/TitlePane",
	"umc/widgets/PasswordInputBox",
	"umc/widgets/Wizard",
	"umc/widgets/Grid",
	"umc/widgets/RadioButton",
	"umc/widgets/ProgressBar",
	"./LiveSearch",
	"umc/i18n/tools",
	"umc/i18n!umc/modules/setup",
	"dojo/NodeList-manipulate"
], function(dojo, declare, lang, array, dojoEvent, domClass, on, Evented, topic, Deferred, all, Memory, Select, Tooltip, focusUtil, styles, timing, dialog, tools, TextBox, CheckBox, ComboBox, Text, Button, TitlePane, PasswordInputBox, Wizard, Grid, RadioButton, ProgressBar, LiveSearch, i18nTools, _) {
	var modulePath = require.toUrl('umc/modules/setup');
	styles.insertCssRule('.umc-ucssetup-wizard-indent', 'margin-left: 27px;');
	styles.insertCssRule('.umcIconInfo', lang.replace('background-image: url({0}/info-icon.png); width: 16px; height: 16px;', [modulePath]));
	styles.insertCssRule('.setupLangField', 'vertical-align: middle; margin: 1px 0 1px 5px;');
	styles.insertCssRule('.umc-setup-page-validation li', 'padding-bottom: 0.75em;');
	styles.insertCssRule('.umc-setup-page-error li', 'padding-bottom: 0.75em;');
	styles.insertCssRule('.umc-setup-page-summary ul', 'margin-top: 0;');
	styles.insertCssRule('.umc-setup-page-summary p', 'margin-top: 0.75em;');
	styles.insertCssRule('.umc-setup-page-software th .dojoxGridRowSelector', 'display: none;');
	styles.insertCssRule('.umc-setup-page-software .umcUCSSetupSoftwareGrid', 'margin-left: 200px;');
	styles.insertCssRule('.umc-setup-page-software .umcPageHelpText', 'margin-left: 200px;');
	styles.insertCssRule('.umc-setup-page-software', lang.replace('background-repeat: no-repeat; background-position: -100px 10px; min-height: 200px; background-position: -10px 65px; background-image: url({0}/software.png);', [modulePath]));
	styles.insertCssRule('.umc-setup-page .city-match td', 'padding-right: 0.5em; padding-bottom: 0.25em;');
	styles.insertCssRule('.umc-setup-page > form > div', 'background-repeat: no-repeat; background-position: 10px 10px; padding-left: 200px; min-height: 200px;');
	array.forEach(['welcome', 'locale', 'domain', 'user', 'network'], function(ipage) {
		var conf = {
			name: ipage,
			path: modulePath
		};
		styles.insertCssRule(
			lang.replace('.umc-setup-page-{name} > form > div', conf),
			lang.replace('background-image: url({path}/{name}.png)', conf)
		);
	});

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
		lastResult: [],
		query: function(query) {
			this.emit('searching', {});
			var pattern = query.label.toString();
			if (pattern.length) {
				pattern = pattern.substring(0, pattern.length - 1);
			}
			var deferred = new Deferred();
			tools.umcpCommand('setup/find_city', {
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

	// taken from: http://stackoverflow.com/a/9221063
	var _regIPv4 =  /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))$/;
	var _regIPv6 = /^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?$/;
	var _regFQDN = /^(?=.{1,255}$)[0-9A-Za-z](?:(?:[0-9A-Za-z]|\b-){0,61}[0-9A-Za-z])?(?:\.[0-9A-Za-z](?:(?:[0-9A-Za-z]|\b-){0,61}[0-9A-Za-z])?)*\.?$/;
	var _regNumber = /^[0-9]+$/;
	var _regBitMask = /^1*0*$/;

	var _regEmailAddress = /^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-.]+$/;
	var _invalidEmailAddressMessage = _('Invalid e-mail address!<br>Expected format is:<i>mail@example.com</i>');
	var _validateEmailAddress = function(email) {
		email = email || '';
		var isEmailAddress = _regEmailAddress.test(email);
		var acceptEmtpy = !email && !this.required;
		return acceptEmtpy || isEmailAddress;
	};

	var _invalidIPAddressMessage = _('Invalid IP address!<br>Expected format is IPv4 or IPv6.');
	var _validateIPAddress = function(ip) {
		ip = ip || '';
		var isIPv4Address = _regIPv4.test(ip);
		var isIPv6Address = _regIPv6.test(ip);
		var acceptEmtpy = !ip && !this.required;
		return acceptEmtpy || isIPv4Address || isIPv6Address;
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

		var isIPv4Address = _regIPv4.test(mask);
		if (!isIPv4Address) {
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
		var isFQDN = _regFQDN.test(hostname);
		var hasNoDots = hostname.indexOf('.') < 0;
		var acceptEmtpy = !hostname && !this.required;
		return acceptEmtpy || (isFQDN && hasNoDots);
	};

	var _invalidFQDNMessage = _('Invalid fully qualified domain name!<br>Expected format: <i>hostname.mydomain.intranet</i>');
	var _validateFQDN = function(fqdn) {
		fqdn = fqdn || '';
		var isFQDN = _regFQDN.test(fqdn);
		var hasEnoughParts = fqdn.split('.').length >= 3;
		var acceptEmtpy = !fqdn && !this.required;
		return acceptEmtpy || (isFQDN && hasEnoughParts);
	};

	var _invalidHostOrFQDNMessage = _('Invalid hostname or fully qualified domain name!<br>Expected format: <i>myhost</i> or <i>hostname.mydomain.intranet</i>');
	var _validateHostOrFQDN = function(hostOrFQDN) {
		hostOrFQDN = hostOrFQDN || '';
		var acceptEmtpy = !hostOrFQDN && !this.required;
		return acceptEmtpy || _validateFQDN(hostOrFQDN) || _validateHostname(hostOrFQDN);
	};

	var _regDN = /^([^=, ]+=[^=, ]+,)*[^=, ]+=[^=, ]+$/;
	var _invalidLDAPBase = _('Invalid LDAP base!<br>Expected format: dc=mydomain,dc=intranet');
	var _validateLDAPBase = function(ldapBase) {
		ldapBase = ldapBase || '';
		var acceptEmtpy = !ldapBase && !this.required;
		return acceptEmtpy || _regDN.test(ldapBase);
	};

	var _umlauts = { 'ä' :'ae', 'Ä' : 'Ae', 'ö' : 'oe', 'Ö' : 'Oe', 'ü' : 'ue', 'Ü' : 'Ue', 'ß' : 'ss', 'Á' : 'A', 'Â' : 'A', 'Ã' : 'A', 'Å' : 'A', 'Æ' : 'AE', 'Ç' : 'C', 'È' : 'E', 'É' : 'E', 'Ê' : 'E', 'Ë' : 'E', 'Ì' : 'I', 'Í' : 'I', 'Î' : 'I', 'Ï' : 'I', 'Ð' : 'D', 'Ñ' : 'N', 'Ò' : 'O', 'Ó' : 'O', 'Ô' : 'O', 'Õ' : 'O', 'Ù' : 'U', 'Ú' : 'U', 'Û' : 'U', 'à' : 'a', 'â' : 'a', 'á' : 'a', 'ã' : 'a', 'æ' : 'ae', 'ç' : 'c', 'è' : 'e', 'é' : 'e', 'ê' : 'e', 'ë' : 'e', 'ì' : 'i', 'í' : 'i', 'î' : 'i', 'ï' : 'i', 'ñ' : 'n', 'ò' : 'o', 'ó' : 'o', 'ô' : 'o', 'ù' : 'u', 'ú' : 'u', 'û' : 'u', 'ý' : 'y', 'ÿ' : 'y', 'Ĉ' : 'C', 'ĉ' : 'c' };

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

	return declare('umc.modules.setup.ApplianceWizard', Wizard, {
		// __systemsetup__ user is logged in at local firefox session
		local_mode: false,

		// original values as return by the load command
		values: {},

		// a timer used it in _cleanup
		// to make sure the session does not expire
		_keepAlive: null,

		autoValidate: false,
		autoFocus: true,

		_gallery: null,
		_appGalleryUpdated: null,
		_nLocaleSettingsConfigured: false,
		_forcedPage: null,
		_progressBar: null,
		_criticalJoinErrorOccurred: false,

		constructor: function(props) {
			lang.mixin(this, props);

			this.pages = [{
				'class': 'umc-setup-page umc-setup-page-welcome',
				name: 'welcome',
				headerText: _('UCS setup'),
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'help',
					content: _('<p>Welcome to Univention Corporate Server (UCS).</p><p>A few questions are needed to complete the configuration process.</p>')
				}, {
					type: Select,
					name: '_language',
					label: _('To proceed, choose your language:'),
					options: _getDecoratedLanguageOptions(),
					value: i18nTools.defaultLang(),
					onChange: lang.hitch(this, function(locale) {
						if (locale != i18nTools.defaultLang()) {
							this.onReload(locale);
						}
					})
				}, {
					type: LiveSearch,
					name: '_search',
					store: new _CityStore(),
					label: _('Enter a city nearby to preconfigure settings such as timezone, system language, keyboard layout.'),
					inlineLabel: _('e.g., Boston...'),
					labelConf: { style: 'margin-top: .75em;' }
				}, {
					type: TitlePane,
					name: 'result',
					content: '',
					title: _('Localization settings'),
					visible: false,
					toggleable: false,
					style: 'min-width: 25em;'
				}]
			}, {
				'class': 'umc-setup-page umc-setup-page-locale',
				name: 'locale',
				headerText: _('Localization settings'),
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'help',
					content: _('Choose your system\'s localization settings.')
				}, {
					type: ComboBox,
					name: 'locale/default',
					label: _('Default system locale'),
					dynamicOptions: {pattern: '*'},
					dynamicValues: 'setup/lang/locales'
				}, {
					type: ComboBox,
					name: 'timezone',
					label: _('Time zone'),
					dynamicValues: 'setup/lang/timezones'
				}, {
					type: ComboBox,
					name: 'locale/keymap',
					label: _('Keyboard layout'),
					dynamicValues: 'setup/lang/keymaps',
					onChange: lang.hitch(this, function(value) {
						if (this.local_mode) {
							tools.umcpCommand('setup/keymap/save', {keymap: value});
						}
					})
				}]
			}, {
				'class': 'umc-setup-page umc-setup-page-domain',
				name: 'role',
				headerText: _('Domain setup'),
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'help',
					content: _('Will the system be the first system of a new UCS domain or shall it join into an existing one?')
				}, {
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_createDomain',
					label: '<b>' + _('Create a new UCS domain') + '</b>',
					checked: true,
					labelConf: { style: 'margin-top: 0; margin-bottom: 0;' }
				}, {
					type: Text,
					name: 'newDomainHelpText',
					content: '<p>' + _('Configure this system as standalone and with a new UCS domain. Additional systems can join the domain later to use account information supplied by this system.') + '</p>',
					labelConf: { 'class': 'umc-ucssetup-wizard-indent' }
				}, {
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_joinDomain',
					label: '<b>' + _('Join into an existing UCS domain') + '</b>',
					labelConf: { style: 'margin-top: 1.5em; margin-bottom: 0;' }
				}, {
					type: Text,
					name: 'joinDomainHelpText',
					content: '<p>' + _('This system will join a group of existing systems which share user and computer accounts, credentials and other trustworthy information.') + '</p>',
					labelConf: { 'class': 'umc-ucssetup-wizard-indent' }
				}, {
					type: Text,
					name: 'ifUnsureHelpText',
					content: _('If unsure, select <i>Create a new UCS domain</i>.'),
					labelConf: { style: 'margin-top: 1.5em;' }
				}]
			}, {
				'class': 'umc-setup-page umc-setup-page-domain',
				name: 'role-nonmaster',
				headerText: _('System role'),
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'help',
					content: _('<p>Specify the type of the system to join into an existing UCS domain. For this, credentials of a valid domain Administrator account will be necessary.</p>')
				}, {
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_roleBackup',
					label: _('<b>Domain controller backup</b>'),
					checked: true,
					labelConf: { style: 'margin-top: 0em; margin-bottom: 0'	}
				}, {
					type: Text,
					name: 'helpBackup',
					content: _('<p>The DC backup is the fallback system for the DC master and can take over the role of the DC master permanently.</p>'),
					labelConf: { 'class': 'umc-ucssetup-wizard-indent' }
				}, {
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_roleSlave',
					label: _('<b>Domain controller slave</b>'),
					labelConf: { style: 'margin-top: 1.5em; margin-bottom: 0'	}
				}, {
					type: Text,
					name: 'helpSlave',
					content: _('<p>DC slave systems are ideal for site servers and distribution of load-intensive services. Local services running on a DC slave can access a local read-only replica of the LDAP database.</p>'),
					labelConf: { 'class': 'umc-ucssetup-wizard-indent' }
				}, {
					type: RadioButton,
					radioButtonGroup: 'role',
					name: '_roleMember',
					label: _('<b>Member server</b>'),
					labelConf: { style: 'margin-top: 1.5em; margin-bottom: 0'	}
				}, {
					type: Text,
					name: 'helpMember',
					content: _('<p>Member servers are server systems without a local LDAP server. Access to domain data here is performed via other servers in the domain.</p>'),
					labelConf: { 'class': 'umc-ucssetup-wizard-indent' }
				}]
			}, {
				'class': 'umc-setup-page umc-setup-page-user',
				name: 'user-master',
				headerText: _('Administrator account information'),
				helpText: '',
				layout: [
					'help',
					'organization',
					'email_address',
					'root_password'
				],
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'help',
					content: _('<p>Enter the name of your organization, an e-mail address to activate UCS and a password for your <i>Administrator</i> account.</p><p>The password is mandatory, it will be used for the domain Administrator as well as for the local superuser <i>root</i>.</p>')
				}, {
					type: TextBox,
					name: 'organization',
					label: _('Organization name'),
					onChange: lang.hitch(this, '_updateOrganizationName')
				}, {
					type: TextBox,
					name: 'email_address',
					label: _('E-mail address to activate UCS') +
						' (<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').showTooltip(event, \'email\');">' +
						_('more information') +
						'</a>)',
					validator: _validateEmailAddress,
					invalidMessage: _invalidEmailAddressMessage
				}, {
					type: PasswordInputBox,
					required: true,
					name: 'root_password',
					label: _('Password')
				}]
			}, {
				'class': 'umc-setup-page umc-setup-page-network',
				name: 'network',
				headerText: _('Domain and host configuration'),
				layout: [
					'helpMaster',
					'helpNonMaster',
					['_fqdn', 'ldap/base'],
					'hostname',
					'root_password',
					'_dhcp',
					['_ip0', '_netmask0'],
					['_ip1', '_netmask1'],
					['_ip2', '_netmask2'],
					['_ip3', '_netmask3'],
					'gateway',
					['nameserver1', 'nameserver2'],
					['dns/forwarder1', 'dns/forwarder2'],
					'proxy/http',
					'configureProxySettings'
				],
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'helpMaster',
					content: _('Configure the new UCS domain and specify the network settings for this system.')
				}, {
					type: Text,
					'class': 'umcPageHelpText',
					name: 'helpNonMaster',
					content: _('Specify hostname as well as a password for the local superuser <i>root</i> and configure network settings for this system.')
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
				}, {
					type: TextBox,
					name: 'hostname',
					label: _('Hostname or fully qualified domain name') +
						' (<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').showTooltip(event, \'hostname\');">' +
						_('more information') +
						'</a>)',
					visible: false,
					required: true,
					validator: _validateHostOrFQDN,
					invalidMessage: _invalidHostOrFQDNMessage
				}, {
					type: PasswordInputBox,
					name: 'root_password',
					label: _('Local root password'),
					visible: false,
					required: this.local_mode
				}, {
					type: CheckBox,
					name: '_dhcp',
					label: _('Obtain IP address automatically (DHCP)'),
					labelConf: { style: 'margin-top: 2em;' },
					onChange: lang.hitch(this, function(value) {
						this._disableNetworkAddressWidgets(value);
						var focused = this.getWidget('network', '_dhcp').focused;
						if (value && focused) {
							// see whether DHCP is working
							this._dhclient();
						}
					})
				}, {
					type: TextBox,
					name: '_ip0',
					label: _('IPv4 address/IPv6 address {interface}'),
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
					label: _('IPv4 address/IPv6 address {interface}'),
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
					label: _('IPv4 address/IPv6 address {interface}'),
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
					label: _('IPv4 address/IPv6 address {interface}'),
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
					required: true,
					invalidMessage: _invalidIPAddressMessage,
					validator: _validateIPAddress,
					labelConf: { style: 'margin-bottom: 2em;' }
				}, {
					type: TextBox,
					name: 'nameserver1',
					label: _('Preferred UCS domain name server'),
					required: true,
					invalidMessage: _invalidIPAddressMessage,
					validator: _validateIPAddress
				}, {
					type: TextBox,
					name: 'nameserver2',
					label: _('Alternate UCS domain name server'),
					invalidMessage: _invalidIPAddressMessage,
					validator: _validateIPAddress
				}, {
					type: TextBox,
					name: 'dns/forwarder1',
					label: _('Preferred external name server'),
					visible: false,
					required: true,
					invalidMessage: _invalidIPAddressMessage,
					validator: _validateIPAddress
				}, {
					type: TextBox,
					name: 'dns/forwarder2',
					label: _('Alternate external name server'),
					visible: false,
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
			}, {
				name: 'software',
				'class': 'umc-setup-page umc-setup-page-software',
				headerText: _('Software configuration'),
				helpText: _('<p>Select UCS software components for installation on this system. This step can be skipped; the components are also available in the Univention App Center in the category <i>UCS components</i>.</p><p>Third-party software (e.g., groupware) is also available through the Univention App Center.</p>')
			}, {
				name: 'validation',
				'class': 'umc-setup-page-validation',
				headerText: _('Validation failed'),
				helpText: _('The following entries could not be validated:'),
				widgets: [{
					type: Text,
					name: 'info',
					content: ''
				}]
			}, {
				name: 'summary',
				'class': 'umc-setup-page-summary',
				headerText: _('Confirm configuration settings'),
				helpText: _('Please confirm the chosen configuration settings which are summarized below.'),
				widgets: [{
					type: Text,
					name: 'info',
					content: ''
				}]
			}, {
				name: 'error',
				'class': 'umc-setup-page-error',
				headerText: _('UCS setup - An error ocurred'),
				helpText: '_',
				widgets: [{
					type: Text,
					name: 'info',
					style: 'font-style:italic;',
					content: ''
				}]
			}, {
				name: 'done',
				'class': 'umc-setup-page umc-setup-page-welcome',
				headerText: _('UCS has been set up successfully'),
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'help',
					content: _('<p>UCS has been successfully set up with the specified settings.</p><p>Click on the button <i>Finish</i> to complete the setup process.</p>')
				}]
			}];
		},

		_isDHCPPreConfigured: function() {
			return array.some(this._getNetworkDevices(), function(idev) {
				var dev = this.values.interfaces[idev];
				return dev && dev.ip4dynamic;
			}, this);
		},

		postCreate: function() {
			this.inherited(arguments);

			// if DHCP is pre-configured, set widgets accordingly
			if (this._isDHCPPreConfigured()) {
				this.getWidget('network', '_dhcp').set('value', true);
				this.getWidget('network', 'gateway').set('value', this.values.gateway);
				this.getWidget('network', 'dns/forwarder1').set('value', this.values['dns/forwarder1']);
				this.getWidget('network', 'dns/forwarder2').set('value', this.values['dns/forwarder2']);

				// set IP addresses/netmasks
				array.forEach(this._getNetworkDevices(), function(idev, i) {
					var devConf = this.values.interfaces[idev] || {};
					var ipWidget = this.getWidget('network', '_ip' + i);
					var maskWidget = this.getWidget('network', '_netmask' + i);
					if (devConf.ip4 && devConf.ip4.length) {
						// ipv4 is configured
						ipWidget.set('value', devConf.ip4[0][0]);
						maskWidget.set('value', devConf.ip4[0][1]);
					}
					else if (devConf.ip6 && devConf.ip6.length) {
						// ipv6 is configured
						ipWidget.set('value', devConf.ip6[0][0]);
						maskWidget.set('value', devConf.ip6[0][1]);
					}
				}, this);
			}
		},

		_dhclient: function() {
			// send out queries for each network device
			var queries = {};
			var dev2index = {};
			array.forEach(this._getNetworkDevices(), function(idev, i) {
				// workaround: use umcpProgressCommand() to make the setup/net/dhclient threaded
				dev2index[idev] = i;
				queries[idev] = tools.umcpProgressCommand(this._progressBar, 'setup/net/dhclient', {
					'interface': idev
				}, false).then(null, function(error) {
					// catch error case to avoid dojo/promise/all canceling all bundled deferreds
					return {};
				});
			}, this);

			// blur current element
			tools.defer(function() {
				if (focusUtil.curNode) {
					focusUtil.curNode.blur();
				}
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
					if (result.is_ucs_nameserver_1) {
						nameserver = nameserver || result.nameserver_1;
					}

					// set received values
					this.getWidget('network', '_ip' + i).set('value', address);
					this.getWidget('network', '_netmask' + i).set('value', netmask);
				}, this);

				// set received gateway/nameserver values
				if (gateway) {
					this.getWidget('network', 'gateway').set('value', gateway);
				}
				if (!this._isRoleMaster() && nameserver) {
					this.getWidget('network', 'nameserver1').set('value', nameserver);
				}

				// did DHCP work?
				if (!hasDHCP) {
					dialog.alert(_('DHCP query failed.'));
					this.getWidget('network', '_dhcp').set('value', false);
				}
			}));
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
				msg = _('A valid e-mail address allows to activate the UCS system for using the Univention App Center. An e-mail with a personalized license key will then be sent to your e-mail address. This license can be uploaded via the license dialog in Univention Management Console.');
			}
			else if (type == 'hostname') {
				msg = _('For a specified host name, the domain name is automatically derived from the domain name server. A fully qualified domain may be necessary for mail server setups with differing domains.<br/>Note that the domain name <b>cannot</b> be changed after the UCS setup wizard has been completed.');
			}
			else if (type == 'proxy') {
				msg = _('A proxy address needs to be specified in the format: <i>http://proxy.mydomain.intranet:3128</i><br/>Proxy access with username and password may be specified via the format: <i>http://username:password@proxy.mydomain.intranet:3128</i>');
			}
			if (msg) {
				_showTooltip(evt.target, msg, evt);
			}
		},

		_addWidgetToPage: function(pageName, widget) {
			var page = this.getPage(pageName);
			if (page._form) {
				page.removeChild(page._form);
			}
			if (!widget.region) {
				widget.region = 'center';
			}
			page.addChild(widget);
		},

		_setupPasswordBoxes: function() {
			// change width to 1/2
			array.forEach(['user-master', 'network'], function(ipage) {
				var passwordWidget = this.getWidget(ipage, 'root_password');
				array.forEach([passwordWidget._firstWidget, passwordWidget._secondWidget], function(iwidget) {
					domClass.remove(iwidget.domNode, 'umcSize-One');
					domClass.add(iwidget.domNode, 'umcSize-Half');
				}, this);
			}, this);
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
					['user-master', 'email_address'],
					['network', 'hostname'],
					['network', 'proxy/http']
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
				serverrole: {
					test: function(val) {
						return !val.length || array.indexOf(val, serverRole) >= 0;
					}
				}
			};

			if (serverRole != 'domaincontroller_master') {
				// hide entries that need to install packages on the DC master
				query.defaultpackagesmaster = {
					test: function(val) {
						return !val.length;
					}
				};
			}

			return query;
		},

		_setupAppGallery: function() {
			this._apps = new Memory({});
			this._gallery = new _Grid({
				moduleStore: this._apps,
				columns: [{
					name: 'name',
					width: 'auto',
					label: _('Software component'),
					formatter: lang.hitch(this, function(value, idx) {
						var item = this._gallery._grid.getItem(idx);
						return lang.replace('<div>{name}</div><div style="color:#818181;">{description}</div>', item);
					})
				}, {
					name: 'longdescription',
					label: ' ',
					width: '50px',
					formatter: function(description) {
						var button = null;
						button = new Button({
							iconClass: 'umcIconInfo',
							callback: function(evt) {
								_showTooltip(button.domNode, description, evt);
							}
						});
						return button;
					}
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
				}
			});
			this._addWidgetToPage('software', this._gallery);
			this._gallery.on('filterDone', lang.hitch(this, function() {
				this._apps.query({is_installed: true}).forEach(lang.hitch(this, function(iitem) {
					var idx = this._gallery._grid.getItemIndex(iitem);
					this._gallery._grid.selection.addToSelection(idx);
				}));
			}));
			tools.umcpCommand('setup/apps/query').then(lang.hitch(this, function(response) {
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
		},

		_setLocaleValues: function(data) {
			if (data.timezone) {
				this.getWidget('locale', 'timezone').setInitialValue(data.timezone);
			}
			if (data.ipv4_nameserver) {
				var forwarderWidget = this.getWidget('network', 'dns/forwarder1');
				if (!forwarderWidget.get('value')) {
					// do not overwrite an already configured value (in case DHCP is preconfigured)
					forwarderWidget.set('value', data.ipv4_nameserver);
				}
			}
			if (data.locale) {
				this.getWidget('locale', 'locale/default').setInitialValue(data.locale);
			}
			if (data.keyboard) {
				this.getWidget('locale', 'locale/keymap').setInitialValue(data.keyboard);
			}
		},

		_setLocaleDefault: function() {
			var defaults = {
				'de-DE': {
					timezone: 'Europe/Berlin',
					locale: 'de_DE.UTF-8:UTF-8',
					keyboard: 'de-latin1'
				},
				'en-US': {
					timezone: 'America/New_York',
					locale: 'en_US.UTF-8:UTF-8',
					keyboard: 'us'
				}
			};
			this._setLocaleValues(defaults[i18nTools.defaultLang()] || {});
		},

		buildRendering: function() {
			this.inherited(arguments);

			// make the session not expire before the user can confirm the
			// cleanup dialog started (and stopped) in _cleanup
			this._keepAlive = new timing.Timer(1000 * 30);
			this._keepAlive.onTick = function() {
				// dont do anything important here, just
				// make sure that umc does not forget us
				// dont even handle errors
				tools.umcpCommand('setup/finished', {}, false);
			};

			// setup the progress bar
			this._progressBar = new ProgressBar();
			this.own(this._progressBar);

			this._setupCitySearch();
			this._setupJavaScriptLinks();
			this._setupPasswordBoxes();
			this._setupNetworkDevices();
			this._setupAppGallery();
			this._setLocaleDefault();
			this._setupFooterButtons();
			this._updateOrganizationName('');
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
			var hostname = this._randomHostName();
			var fqdn = lang.replace('{0}.{1}.intranet', [hostname, organization]);
			this.getWidget('network', '_fqdn').set('value', fqdn);
			this.getWidget('network', 'hostname').set('value', hostname);
		},

		_updateLDAPBase: function(fqdn) {
			fqdn = fqdn.replace(/ /g, '');  // remove all spaces from fqdn
			var fqdnParts = fqdn.split('.').slice(1);
			var ldapBaseParts = array.map(fqdnParts, function(ipart) {
				return 'dc=' + ipart;
			});
			var ldapBase = ldapBaseParts.join(',');
			var ldapBaseWidget = this.getWidget('network', 'ldap/base');
			ldapBaseWidget.set('value', ldapBase);
		},

		_updateNetworkPage: function() {
			// default visibilities for the role DC master
			var visibilities = {
				helpMaster: true,
				helpNonMaster: false,
				_fqdn: true,
				hostname: false,
				'ldap/base': true,
				root_password: false,
				nameserver1: false,
				nameserver2: false,
				'dns/forwarder1': true,
				'dns/forwarder2': true
			};
			var role = this._getRole();
			if (role == 'domaincontroller_backup' || role == 'domaincontroller_slave') {
				visibilities = {
					helpMaster: false,
					helpNonMaster: true,
					_fqdn: false,
					hostname: true,
					'ldap/base': false,
					root_password: true,
					nameserver1: true,
					nameserver2: true,
					'dns/forwarder1': true,
					'dns/forwarder2': true
				};
			}
			else if (role == 'memberserver') {
				visibilities = {
					helpMaster: false,
					helpNonMaster: true,
					_fqdn: false,
					hostname: true,
					'ldap/base': false,
					root_password: true,
					nameserver1: true,
					nameserver2: true,
					'dns/forwarder1': false,
					'dns/forwarder2': false
				};
			}
			tools.forIn(visibilities, function(iid, ivisible) {
				var iwidget = this.getWidget('network', iid);
				iwidget.set('visible', ivisible);
			}, this);
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
			if (city.default_keyboard) {
				city.keyboard = city.default_keyboard;
				var layoutWidget = this.getWidget('locale', 'locale/keymap');
				array.some(layoutWidget.getAllItems(), function(ilayout) {
					 if (ilayout.id == city.keyboard) {
						// found matching layout -> break loop
						defaultKeyboardLabel = ilayout.label;
						nSettingsConfigured++;
						return true;
					 }
				});
			}
			msg += _('<tr><td>Keyboard layout:</td><td>%s</td></tr>', defaultKeyboardLabel);
			msg += '</table>';
			resultWidget.set('content', msg);
			resultWidget.set('visible', true);
			this._setLocaleDefault(); // set a fallback for unknown values
			this._setLocaleValues(city);

			// append button to change locale settings
			var changeSettingsButton = new Button({
				style: 'margin-top: 0.5em; float: right;',
				label: _('Adapt settings'),
				onClick: lang.hitch(this, '_next', 'welcome-adapt-locale-settings')
			});
			resultWidget.addChild(changeSettingsButton);

			// save how many settings could be configured
			this._nLocaleSettingsConfigured = nSettingsConfigured;
		},

		_updateNetwork: function(idx, ip) {
			ip = lang.trim(ip);
			var isIPv4Address = _regIPv4.test(ip);
			if (isIPv4Address) {
				var ipParts = ip.split('.');
				var netmask = '255.255.255.0';
				var netmaskWidget = this.getWidget('network', '_netmask' + idx);
				netmaskWidget.set('value', netmask);

				var gatewayWidget = this.getWidget('network', 'gateway');
				if (idx === 0 && !gatewayWidget.get('value')) {
					// suggest a gateway address for the first IP address
					var gateway = ipParts.slice(0, -1).join('.') + '.1';
					gatewayWidget.set('value', gateway);
				}
			}
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

			// system role
			msg += '<p><b>' + _('UCS configuration') + '</b>: ';
			if (vals['server/role'] == 'domaincontroller_master') {
				msg += _('A new UCS domain will be created.');
			}
			else {
				var role = {
					'domaincontroller_backup': _('DC Backup'),
					'domaincontroller_slave': _('DC Slave'),
					'memberserver': _('Member server')
				}[vals['server/role']];
				msg += _('This sytem will join an existing UCS domain with the role <i>%s</i>.', role);
			}
			msg += '</p>';

			// localization settings
			msg += '<p><b>' + _('Localization settings') + '</b></p>';
			msg += '<ul>';
			array.forEach(['locale/default', 'timezone', 'locale/keymap'], function(ikey) {
				var iwidget = this.getWidget('locale', ikey);
				var item = _getItem(iwidget.getAllItems(), vals[ikey]);
				_append(iwidget.label, item.label);
			}, this);
			msg += '</ul>';

			// administrator account
			if (this._isRoleMaster()) {
				msg += '<p><b>' + _('Administrator account information') + '</b></p>';
				msg += '<ul>';
				_append(_('Organization name'), vals.organization);
				_append(_('E-mail address to activate UCS'), vals.email_address);
				msg += '</ul>';
			}

			// network settings
			msg += '<p><b>' + _('Domain and host configuration') + '</b></p>';
			msg += '<ul>';
			_append(_('Fully qualified domain name'), _vals._fqdn);
			if (_validateHostname(_vals.hostname) && guessedDomainName) {
				// if the backend gave us a guess for the domain name, show it here
				_append(_('Fully qualified domain name'), _vals.hostname + '.' + guessedDomainName);
			}
			else {
				// 'hostname' can be host name or FQDN... choose the correct label
				var hostLabel = _validateFQDN(_vals.hostname) ? _('Fully qualified domain name') : _('Hostname');
				_append(hostLabel, _vals.hostname);
			}
			_append(_('LDAP base'), vals['ldap/base']);
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

			var nameservers = array.filter([vals.nameserver1, vals.nameserver2], function(inameserver) {
				return inameserver;
			}).join(', ');
			_append(_('UCS domain name server'), nameservers);

			var forwarders = array.filter([vals['dns/forwarder1'], vals['dns/forwarder2']], function(iforwarder) {
				return iforwarder;
			}).join(', ');
			_append(_('External name server'), forwarders);

			_append(_('HTTP proxy'), vals['proxy/http']);
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
				msg += ientry.message;
				msg += '</li>';
			}, this);
			msg += '</ul>';

			// display validation information
			this.getWidget('validation', 'info').set('content', msg);
		},

		_updateErrorPage: function(details, critical) {
			var msg = '<ul>';
			array.forEach(details, function(idetail) {
				msg += '<li>' + idetail + '</li>';
			});
			msg += '</ul>';

			var helpText = '';
			if (critical) {
				helpText = '<p>' + _('The system join process failed. The following information will give some more details on which exact problem occurred during the setup process.') + '</p>';
				msg += '<p>' + _('You may reconfigure the settings and restart the join process. You may end the wizard and, if necessary, join the system later via the UMC module <i>Domain join</i>.') + '</p>';
			} else {
				helpText = '<p>' + _('The system join was successful, however, the following errors occurred while applying the configuration settings.') + '</p>';
				msg += '<p>' + _('The settings can always be adpated in the UMC module <i>Basic settings</i>. Please confirm now to complete the process.') + '</p>';
			}

			// display validation information
			this.getPage('error').set('helpText', helpText);
			this.getWidget('error', 'info').set('content', msg);

			// save the state
			this._criticalJoinErrorOccurred = critical;
		},

		_validateWithServer: function() {
			var vals = this.getValues();
			this.standby(true);
			return tools.umcpCommand('setup/validate', { values: vals }).then(lang.hitch(this, function(response) {
				this.standby(false);
				var allValid = true;
				var result = {};
				array.forEach(response.result, function(ientry) {
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
			var showRoleSelection = array.indexOf(this.visiblePages, 'SystemRolePage') > -1;
			var createNewDomain = this.getWidget('_createDomain').get('value');
			return createNewDomain || !showRoleSelection;
		},

		_isPageForRole: function(pageName) {
			if (pageName.indexOf('-master') >= 0) {
				return this._isRoleMaster();
			}
			if (pageName.indexOf('-nonmaster') >= 0) {
				return !this._isRoleMaster();
			}
			return true;
		},

		isPageVisible: function(pageName) {
			if (!this._isPageForRole(pageName)) {
				return false;
			}
			if (pageName == 'locale' && this._nLocaleSettingsConfigured == 3) {
				// no need to display page for locale settings
				return false;
			}

			// support black and white listing for software page and system role page
			// as it was the case prior to Bug #34484
			if (pageName == 'software') {
				var showSoftwarePage = array.indexOf(this.visiblePages, 'SoftwarePage') > -1;
				return showSoftwarePage;
			}
			if (pageName.indexOf('role') === 0) {
				var showRoleSelection = array.indexOf(this.visiblePages, 'SystemRolePage') > -1;
				return showRoleSelection;
			}

			// default
			return true;
		},

		_getLinkLocalDHCPAddresses: function() {
			if (this.getWidget('network', '_dhcp').get('value')){
				var fallbackDevices = [];
				array.forEach(this._getNetworkDevices(), function(idev, i) {
					var ip = this.getWidget('network', '_ip' + i).get('value');
					var mask = this.getWidget('network', '_netmask' + i).get('value');
					if ((ip.indexOf('169.254') === 0) && (mask=='255.255.0.0')) {
						fallbackDevices.push([
							name: idev,
							ip: ip
						]);
					}
				}, this);
				return fallbackDevices;
			}
		},

		_validatePage: function(pageName) {
			if (pageName == 'software') {
				// validate software components
				var packages = {};
				array.forEach(this._gallery.getSelectedItems(), function(iapp) {
					var ipackages = [].concat(iapp.defaultpackages, iapp.defaultpackagesmaster);
					array.forEach(ipackages, function(ipackage) {
						packages[ipackage] = true;
					});
				});
				if (packages['univention-samba'] && packages['univention-samba4']) {
					_alert(_('<p>It is not possible to install Samba 3 and Samba 4 on one system.</p><p>Please select only one of these components.</p>'));
					return false;
				}
				if (packages['univention-virtual-machine-manager-node-kvm'] && packages['univention-virtual-machine-manager-node-xen']) {
					_alert(_('<p>It is not possible to install KVM and XEN components on one system.</p><p>Please select only one of these components.</p>'));
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
			if (pageName == 'user-master' || pageName == 'network') {
				var passwordWidget = this.getWidget(pageName, 'root_password');
				var password = passwordWidget.get('value');
				if (passwordWidget.get('visible') && password && password.length < 8) {
					passwordWidget.focus();
					_alert(_('The root password is too short. For security reasons, your password must contain at least 8 characters.'));
					return false;
				}
			}

			// check network device configuration
			if (pageName == 'network') {
				var _vals = this._gatherVisibleValues();
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
			var _credentials = lang.hitch(this, function() {
				var msg = '<p>' + _('The specified settings will be applied to the system and the system will be joined into the domain. Please enter username and password of a domain administrator account.') + '</p>';
				return dialog.confirmForm({
					widgets: [{
						name: 'text',
						type: Text,
						content: msg
					}, {
						name: 'username',
						type: 'TextBox',
						label: _('Username'),
						value: 'Administrator'
					}, {
						name: 'password',
						type: 'PasswordBox',
						label: _('Password')
					}],
					layout: [ 'text', 'username', 'password' ],
					title: _('Domain admin credentials'),
					submit: _('Join domain'),
					cancel: _('Cancel'),
					style: 'max-width: 400px;'
				});
			});

			// function to save data
			var _join = lang.hitch(this, function(values, username, password) {
				var deferred = new Deferred();

				// send save command to server
				this._progressBar.reset(_('Initialize the configuration process ...'));
				this.standby(true, this._progressBar);
				tools.umcpCommand('setup/join', {
					values: values,
					// make sure that the username/password are null and not undefined
					// ... server cannot handle "undefined"
					username: username || null,
					password: password || null
				}, false);

				// poll whether script has finished
				tools.defer(lang.hitch(this, function() {
					this._progressBar.auto(
						'setup/finished',
						{},
						lang.hitch(deferred, 'resolve'),
						null,
						_('Configuration finished'),
						true
					);
				}), 500);

				return deferred.then(lang.hitch(this, function() {
					this.standby(false);
				}));
			});

			var _hasJoinErrors = lang.hitch(this, function() {
				this.standby(false);
				var errors = this._progressBar.getErrors();
				if (errors.errors.length) {
					this._updateErrorPage(errors.errors, errors.critical);
					return false;
				}
				return true;
			});

			// chain all methods together
			var deferred = null;
			var values = this.getValues();
			if (values['server/role'] == 'domaincontroller_master') {
				deferred = _join(values);
			}
			else {
				// for any other role than DC master, we need domain admin credentials
				deferred = _credentials();
				deferred = deferred.then(function(opt) {
					return _join(values, opt.username, opt.password);
				});
			}
			deferred = deferred.then(_hasJoinErrors);
			return deferred;
		},

		_forcePageTemporarily: function(pageName) {
			this._forcedPage = pageName;
			tools.defer(lang.hitch(this, function() {
				// reset the _forcedPage variable to allow a page change again
				this._forcedPage = null;
			}), 500);
			return pageName;
		},

		_updateButtons: function(pageName) {
			this.inherited(arguments);
			var buttons = this._pages[pageName]._footerButtons;
			if (pageName == 'validation') {
				domClass.add(buttons.next.domNode, 'dijitHidden');
				domClass.add(buttons.previous.domNode, 'umcSubmitButton');
			}
		},

		next: function(pageName) {
			// disallow page changing more than every 500 milliseconds (Bug #27734)
			if (this._forcedPage) {
				return this._forcedPage;
			}
			topic.publish('/umc/actions', this.moduleID, 'wizard', pageName, 'next');

			// validation of form fields
			if (!this._validatePage(pageName)) {
				return this._forcePageTemporarily(pageName);
			}

			// start/stop timer
			var nextPage = this.inherited(arguments);
			var keepSessionAlive = (nextPage == 'error' || nextPage == 'done');
			if (keepSessionAlive && !this._keepAlive.isRunning) {
				this._keepAlive.start();
			}
			if (!keepSessionAlive && this._keepAlive.isRunning) {
				this._keepAlive.stop();
			}

			// update display information
			if (nextPage == 'network') {
				this._updateNetworkPage();
			}

			// check dhcp config
			if (pageName == 'network'){
				if (this.getWidget('network', '_dhcp').get('value')) {
					var fallbackDevices = this._getLinkLocalDHCPAddresses();
					if (fallbackDevices.devices.length) {
						var devicesStr = array.map(fallbackDevices, function(idev) {
							return lang.replace('<li><b>{name}:</b> {ip}</li>', idev);
  						}).join('\n').
	  					var msg = _('<p>One or more network interfaces could not obtain an IP address via DHCP. These interfaces will use automatic generated private addresses instead (APIPA).</p> <ul> %s </ul> <p>Please adjust your DHCP settings or confirm use of private address(es).</p>', devicesStr);
						var buttonLabel = _('Continue with 169.254.*.* addresse(s)')
						var allDevices = this._getNetworkDevices();
						if (fallbackDevices.length === allDevices.length ) {
							msg = _('<p>With the current settings <b> no </b> internet access is available.</p><p>Because of this some functions like the Appcenter or software-updates will not be accessible</p>') + msg;
							buttonLabel = ('Continue <b>without</b> internet access');
						}
						return dialog.confirm(msg, [{
							label: _('Cancel'),
							name: pageName
						}, {
							label: buttonLabel,
							'default': true,
							name: nextPage
						}], _('Warning')).then(lang.hitch(this, function(response) {
						return this._forcePageTemporarily(response);
						}));
					}
				}
			}

			if (nextPage == 'software') {
				this._updateAppGallery();
			}

			// extra handling for specific pages
			if (pageName == 'welcome-adapt-locale-settings') {
				return this._forcePageTemporarily('locale');
			}

			// confirm empty passwords (if not required)
			if (pageName == 'user-master' || pageName == 'network') {
				var passwordWidget = this.getWidget(pageName, 'root_password');
				var password = passwordWidget.get('value');
				if (passwordWidget.get('visible') && !password) {
					return dialog.confirm(_('Root password empty. Continue?'), [{
						label: _('Cancel'),
						name: pageName
					}, {
						label: _('Continue'),
						'default': true,
						name: nextPage
					}], _('Warning')).then(lang.hitch(this, function(response) {
						return this._forcePageTemporarily(response);
					}));
				}
			}

			// update summary page
			if (nextPage == 'validation') {
				return this._validateWithServer().then(lang.hitch(this, function(response) {
					// jump to summary page if everything is fine...
					// else display validation errors
					if (response.isValid) {
						this._updateSummaryPage(response);
						return 'summary';
					}
					return 'validation';
				}), function(err) {
					// fallback -> the error will be displayed anyways...
					// stay on the current page
					return pageName;
				});
			}
			if (pageName == 'summary') {
				return this.join().then(function(success) {
					return success ? 'done' : 'error';
				});
			}
			return this._forcePageTemporarily(nextPage);
		},

		previous: function(pageName) {
			// disallow page changing more than every 500 milliseconds (Bug #27734)
			if (this._forcedPage) {
				return this._forcedPage;
			}
			topic.publish('/umc/actions', this.moduleID, 'wizard', pageName, 'previous');

			// stop timer
			if (this._keepAlive.isRunning) {
				this._keepAlive.stop();
			}

			if (pageName == 'error' || pageName == 'summary') {
				var previousPage = this.isPageVisible('software') ? 'software' : 'network';
				return this._forcePageTemporarily(previousPage);
			}
			return this._forcePageTemporarily(this.inherited(arguments));
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
			if (pageName == 'error') {
				return this._criticalJoinErrorOccurred;
			}
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
			return _vals;
		},

		_getRole: function() {
			var _vals = this._gatherVisibleValues();
			var showRoleSelection = array.indexOf(this.visiblePages, 'SystemRolePage') > -1;
			if (_vals._createDomain || !showRoleSelection) {
				return 'domaincontroller_master';
			}
			else if (_vals._roleBackup) {
				return 'domaincontroller_backup';
			}
			else if (_vals._roleSlave) {
				return 'domaincontroller_slave';
			}
			else {
				return 'memberserver';
			}
		},

		getValues: function() {
			// network configuration
			var _vals = this._gatherVisibleValues();
			var vals = {};
			if (this._isDHCPPreConfigured() && _vals._dhcp) {
				// nothing to do... leave the preconfigured settings
			}
			else {
				// prepare values for network interfaces
				vals.interfaces = {};
				array.forEach(this._getNetworkDevices(), function(idev, i) {
					// set primary interface
					if (i === 0) {
						vals['interfaces/primary'] = idev;
					}

					if (_vals._dhcp) {
						// activate DHCP configuration
						vals.interfaces[idev] = {
							name: idev,
							interfaceType: 'Ethernet',
							ip4dynamic: true
						};
					}
					else {
						// make sure valid values are set
						var iip = _vals['_ip' + i];
						var imask = _vals['_netmask' + i];
						if (!iip || !imask) {
							return;
						}

						// prepare interface entry
						var iconf = {
							name: idev,
							interfaceType: 'Ethernet',
							ip4dynamic: false
						};
						if (_regIPv4.test(iip)) {
							// IPv4 address
							iconf.ip4 = [[iip, imask]];
							iconf.ip6 = [];
						} else {
							// IPv6 address
							iconf.ip4 = [];
							iconf.ip6 = [[iip, imask, 'default']];
						}
						vals.interfaces[idev] = iconf;
					}
				});
			}

			// handle ipv6 gateway
			if (_regIPv6.test(_vals.gateway)) {
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
				packages = packages.concat(iapp.defaultpackages, iapp.defaultpackagesmaster);
			});
			vals.components = packages;

			// prepare the dictionary with final values
			tools.forIn(_vals, function(ikey, ival) {
				if (typeof ikey == "string" && ikey.indexOf('_') !== 0 && ival) {
					// ignore values starting with '_'
					vals[ikey] = ival;
				}
			});
			return vals;
		},

		destroy: function() {
			if (this._keepAlive.isRunning) {
				this._keepAlive.stop();
			}
			this.inherited(arguments);
		}
	});
});
