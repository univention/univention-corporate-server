/*
 * Copyright 2012-2014 Univention GmbH
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
	"dojo/dom-class",
	"dojo/on",
	"dojo/topic",
	"dojo/Deferred",
	"dojo/when",
	"dojox/html/styles",
	"dijit/form/RadioButton",
	"umc/dialog",
	"umc/widgets/ProgressBar",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/ExpandingTitlePane",
	"umc/widgets/Module",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/PasswordBox",
	"umc/widgets/CheckBox",
	"umc/widgets/Wizard",
	"./adconnector2/RadioButtons",
	"umc/i18n!umc/modules/adconnector2"
], function(declare, lang, array, domClass, on, topic, Deferred, when, styles, RadioButton, dialog, ProgressBar, tools, Page, Form, ExpandingTitlePane, Module, Text, TextBox, PasswordBox, CheckBox, Wizard, RadioButtons, _) {
	var modulePath = require.toUrl('umc/modules/adconnector2');
	styles.insertCssRule('.umc-adconnector-page > form > div', 'background-repeat: no-repeat; background-position: 10px 0px; padding-left: 200px; min-height: 200px;');
	styles.insertCssRule('.umc-adconnector-page .umcLabelPaneCheckBox', 'display: block !important;');
	array.forEach(['start', 'credentials', 'config', 'info', 'syncconfig', 'syncconfig-left', 'syncconfig-right', 'syncconfig-left-right', 'msi', 'finished'], function(ipage) {
		var conf = {
			name: ipage,
			path: modulePath
		};
		styles.insertCssRule(
			lang.replace('.umc-adconnector-page-{name} > form > div', conf),
			lang.replace('background-image: url({path}/{name}.png)', conf)
		);
	});

	var _Wizard = declare("umc.modules.adconnector2.Wizard", [ Wizard ], {
		autoValidate: true,
		autoFocus: true,

		constructor: function() {
			this.pages = [{
				'class': 'umc-adconnector-page-start umc-adconnector-page',
				name: 'start',
				headerText: _('Active Directory Connector'),
				widgets: [{
					type: Text,
					name: 'help',
					content: _('<p>This wizards guides the configuration of the connection with an existing Active Directory domain.</p><p>There are two possible ways:</p>')
				}, {
					type: RadioButtons,
					name: 'syncmode',
					staticValues: [{
						id: 'partOfAD',
						label: _('Configure UCS as part of the Active Directory domain (recommended).')
					}, {
						id: 'syncWithAD',
						label: _('Synchronisation of account data between an Active Directory and a UCS domain.')
					}]
				}, {
					type: Text,
					name: 'help2',
					content: _('<p>Use the recommended first option if Active Directory will be the principal domain. Domain users can directly access applications that are installed on UCS.</p><p>Use the second option for more complex szenarios which necessitate that Active Directory and UCS domains exist in parallel.</p>')
				}]
			}, {
				'class': 'umc-adconnector-page-credentials umc-adconnector-page',
				name: 'credentials',
				headerText: _('Active Directory domain credentials'),
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'help',
					content: _('To proceed with the configuration of the connection, enter Active Directory domain information:')
				}, {
					type: TextBox,
					name: 'ip',
					required: true,
					label: _('Address of Active Directory domain controller')
				}, {
					type: TextBox,
					name: 'username',
					required: true,
					label: _('Active Directory account'),
					value: 'Administrator'
				}, {
					type: PasswordBox,
					name: 'password',
					required: true,
					label: _('Active Directory password')
				}]
			}, {
				'class': 'umc-adconnector-page-info umc-adconnector-page',
				name: 'partOfADConfig',
				headerText: _('Configuration of UCS as part of Active Directory domain'),
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'help',
					content: _('<p>A Windows 2008 R2 Active Directory domain with the domainname <i>example.org</i> has been found. The server <i>admaster</i> (10.200.8.237) will be used as Active Directory domain controller.</p><p>The following domain accounts have been found:</p><ul><li>13 user accounts</li><li>3 computer accounts</li><li>9 groups</li></ul><p>Click "Next" to inititate the connection.</p>')
				}]
			}, {
				'class': 'umc-adconnector-page-finished umc-adconnector-page',
				name: 'partOfADFinished',
				headerText: _('Completion of Active Directory Connector'),
				widgets: [{
					type: Text,
					name: 'help',
					content: _('<p>Congratulations, Univention Corporate Server has been successfully configured to be part of a Active Directory domain.</p><p>The UCS server is now ready for usage, and domain account information are now available.</p>')
				}]
			}, {
				'class': 'umc-adconnector-page-syncconfig umc-adconnector-page',
				name: 'syncWithADConfig',
				headerText: _('Configuration of Active Directory domain synchronisation'),
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'help',
					content: _('Specify the synchronisation direction between the UCS domain and the given Active Directory domain.')
				}, {
					type: RadioButtons,
					name: 'syncmode',
					staticValues: [{
						id: 'syncAD2UCS',
						label: _('Unidirectional synchronisation of Active Directory to UCS.'),
					}, {
						id: 'syncUCS2AD',
						label: _('Unidirectional synchronisation of UCS to Active Directory.'),
					}, {
						id: 'syncBidirectional',
						label: _('Bidirectional synchronisation of UCS and Active Directory.'),
					}],
					onChange: lang.hitch(this, function(value) {
						var map2img = {
							'default': '',
							syncAD2UCS: '-right',
							syncUCS2AD: '-left',
							syncBidirectional: '-left-right'
						};
						var syncmode = this.getWidget('syncWithADConfig', 'syncmode').get('value');
						var page = this.getPage('syncWithADConfig');
						tools.forIn(map2img, lang.hitch(this, function(ikey, ival) {
							var cssClass = 'umc-adconnector-page-syncconfig' + ival;
							var useClass = syncmode == ikey;
							domClass.toggle(page.domNode, cssClass, useClass);
						}));
					})
				}]
			}, {
				'class': 'umc-adconnector-page-info umc-adconnector-page',
				name: 'syncWithADInfo',
				headerText: _('Active Directory domain information'),
				widgets: [{
					type: Text,
					name: 'help',
					content: _('<p>A Windows 2008 R2 Active Directory domain with the domainname <i>example.org</i> has been found. The server <i>admaster</i> (10.200.8.237) will be used as Active Directory domain controller.</p><p>The following domain accounts have been found:</p><ul><li>13 user accounts</li><li>9 groups</li></ul>')
				}]
			}, {
				'class': 'umc-adconnector-page-msi umc-adconnector-page',
				name: 'syncWithADMsi',
				headerText: _('Installation of password service'),
				widgets: [{
					type: Text,
					name: 'help',
					content: _('<p>The MSI files are the installation files for the password service and can be started by double clicking on it. The package is installed in the <b>C:&#92;Windows&#92;UCS-AD-Connector</b> directory automatically. Additionally, the password service is integrated into the Windows environment as a system service, which means the service can be started automatically or manually.</p><ul><li><a>ucs-ad-connector.msi</a><br>Installation file for the password service for <b>32bit</b> Windows.<br>It can be started by double clicking on it.</li><li><a>ucs-ad-connector-64bit.msi</a><br>Installation file for the password service for <b>64bit</b> Windows.<br>It can be started by double clicking on it.</li><li><a>vcredist_x86.exe</a><br>Microsoft Visual C++ 2010 Redistributable Package (x86) - <b>Must</b> be installed on a <b>64bit</b> Windows.</li></ul><p>After installing the password service, click "Next" to initiate the synchronisation process.</p>')
				}]
			}, {
				'class': 'umc-adconnector-page-finished umc-adconnector-page',
				name: 'syncWithADFinished',
				headerText: _('Completion of Active Directory Connector'),
				widgets: [{
					type: Text,
					name: 'help',
					content: _('<p>Congratulations, the synchronisation of Univention Corporate Server and Active Directory has been succesfully initiated.</p><p>The UCS server is now ready for usage, and domain account information are now available.</p>')
				}]
			}];
		},

		buildRendering: function() {
			this.inherited(arguments);
			var syncmodeWidget = this.getWidget('start', 'syncmode');
		},

		next: function(pageName) {
			var nextPage = this.inherited(arguments);
			var syncmode = this.getWidget('start', 'syncmode').get('value');
			if (pageName == 'credentials') {
				if (syncmode == 'syncWithAD') {
					return 'syncWithADConfig';
				}
			}
			if (pageName == 'partOfADConfig') {
				return this._startUCSJoinInAD().then(function() {
					return nextPage;
				});
			}
			if (pageName == 'syncWithADMsi') {
				return this._startADSync().then(function() {
					return nextPage;
				});
			}
			if ((pageName == 'credentials' && syncmode == 'partOfAD')
				|| (pageName == 'syncWithADConfig' && syncmode == 'syncWithAD')) {
				return this._queryDomainInfo().then(function() {
					return nextPage;
				});
			}
			return nextPage;
		},

		previous: function(pageName) {
			if (pageName.indexOf('Config') >= 0) {
				return 'credentials';
			}
			return this.inherited(arguments);
		},

		hasNext: function(pageName) {
			return pageName.indexOf('Finished') < 0;
		},

		hasPrevious: function(pageName) {
			return pageName.indexOf('Finished') < 0;
		},

		canCancel: function(pageName) {
			return pageName.indexOf('Finished') < 0;
		},

		_timeout: function(seconds, percentage, message) {
			var _deferred = new Deferred();
			setTimeout(lang.hitch(this, function() {
				this.progressBar.setInfo(null, message, percentage);
				_deferred.resolve()
			}), seconds * 1000);
			return _deferred;
		},

		_startUCSJoinInAD: function() {
			this.progressBar.reset(_('UCS join in Active Directory domain'));
			this.standby(true, this.progressBar);
			var self = this;
			return this._timeout(0, 0, _('Contacting Active Directory server')).then(function() {
				return self._timeout(1, 10, _('Authentification with credentials'));
			}).then(function() {
				return self._timeout(1, 20, _('Querying certificates'));
			}).then(function() {
				return self._timeout(2, 40, _('Preparing join'));
			}).then(function() {
				return self._timeout(2, 60, _('Joining the domain'));
			}).then(function() {
				return self._timeout(2, 80, _('Updating local system'));
			}).then(function() {
				return self._timeout(1, 100, _('Cleaning up'));
			}).then(function() {
				return self.standby(false);
			});
		},

		_startADSync: function() {
			this.progressBar.reset(_('Initiating synchronisation with Active Directory domain'));
			this.standby(true, this.progressBar);
			var self = this;
			return this._timeout(0, 0, _('Contacting Active Directory server')).then(function() {
				return self._timeout(1, 10, _('Authentification with credentials'));
			}).then(function() {
				return self._timeout(1, 20, _('Validating service configuration'));
			}).then(function() {
				return self._timeout(3, 40, _('Quering domain accounts'));
			}).then(function() {
				return self._timeout(2, 70, _('Starting synchronisation service'));
			}).then(function() {
				return self._timeout(1, 100, _('Cleaning up'));
			}).then(function() {
				return self.standby(false);
			});
		},

		_queryDomainInfo: function() {
			this.progressBar.reset(_('Querying Active Directory domain information'));
			this.standby(true, this.progressBar);
			this.progressBar._progressBar.set('value', Infinity);
			var self = this;
			return this._timeout(0, null, _('Contacting Active Directory server')).then(function() {
				return self._timeout(1, null, _('Querying domain information'));
			}).then(function() {
				return self._timeout(1, null, _('Querying user accounts'));
			}).then(function() {
				return self._timeout(1, null, _('Querying computer accounts'));
			}).then(function() {
				return self.standby(false);
			});
		}
	});

	return declare("umc.modules.adtakeover2", Module , {
		unique: true,

		buildRendering: function() {
			var progressBar = new ProgressBar({});
			this.inherited(arguments);

			this.wizard = new _Wizard({
				progressBar: progressBar
			});
			this.addChild(this.wizard);
			this.wizard.on('Finished', lang.hitch(this, function() {
				topic.publish('/umc/tabs/close', this);
			}));
			this.wizard.on('Cancel', lang.hitch(this, function() {
				topic.publish('/umc/tabs/close', this);
			}));
		}

	});
});
