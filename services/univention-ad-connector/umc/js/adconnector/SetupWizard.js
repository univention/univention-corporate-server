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
/*global define require */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dojo/topic",
	"dojox/html/styles",
	"dojox/timing/_base",
	"umc/dialog",
	"umc/widgets/ProgressBar",
	"umc/tools",
	"umc/modules/lib/server",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/Uploader",
	"umc/widgets/PasswordBox",
	"umc/widgets/Wizard",
	"./RadioButtons",
	"umc/i18n!umc/modules/adconnector"
], function(declare, lang, array, domClass, topic, styles, timing, dialog, ProgressBar, tools, server, Text, TextBox, Uploader, PasswordBox, Wizard, RadioButtons, _) {
	styles.insertCssRule('.umc-adconnector-page .umcPageNav > .umcPageHelpText', 'background-repeat: no-repeat; background-position: 10px 0px; padding-top: 180px; min-height: 180px;');
	styles.insertCssRule('.umc-adconnector-page .umcLabelPaneCheckBox', 'display: block !important;');
	array.forEach(['start', 'credentials', 'config', 'security', 'certificate', 'syncconfig', 'syncconfig-left', 'syncconfig-right', 'syncconfig-left-right', 'msi', 'finished'], function(ipage) {
		var imageUrl = require.toUrl(lang.replace('umc/modules/adconnector/{0}.png', [ipage]));
		styles.insertCssRule(
			lang.replace('.umc-adconnector-page-{0} .umcPageNav > .umcPageHelpText', [ipage]),
			lang.replace('background-image: url({0})', [imageUrl])
		);
	});

	var _paragraph = function() {
		var html = '';
		array.forEach(arguments, function(para) {
			html += '<p>' + para + '</p>';
		});
		return html;
	};

	var version = tools.status('ucsVersion').split('-')[0];
	return declare("umc.modules.adconnector.SetupWizard", [ Wizard ], {
		autoValidate: true,
		autoFocus: true,
		_progressBar: null,
		_keepSessionAlive: null,
		_adDomainInfo: null,

		constructor: function() {
			this.pages = [{
				'class': 'umc-adconnector-page-start umc-adconnector-page',
				name: 'start',
				headerText: _('Active Directory Connection'),
				helpText: ' ',
				widgets: [{
					type: Text,
					name: 'help',
					content: _('<p>This wizards guides the configuration of the connection with an existing Active Directory domain.</p><p>There are two exclusive options:</p>')
				}, {
					type: RadioButtons,
					name: 'mode',
					staticValues: [{
						id: 'admember',
						label: _('Configure UCS as part of an Active Directory domain (recommended).')
					}, {
						id: 'adconnector',
						label: _('Synchronisation of account data between an Active Directory and this UCS domain.')
					}]
				}, {
					type: Text,
					name: 'help2',
					content: _paragraph(
						_('Use the recommended first option if Active Directory will be the principal domain. Domain users can directly access applications that are installed on UCS.'),
						_('Use the second option for more complex scenarios which necessitate that Active Directory and UCS domains exist in parallel.')
					)
				}]
			}, {
				'class': 'umc-adconnector-page-credentials umc-adconnector-page',
				name: 'credentials-admember',
				headerText: _('Active Directory domain credentials'),
				helpText: ' ',
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'help',
					content: _('Enter the Active Directory domain information to join the domain.')
				}, {
					type: TextBox,
					name: 'ad_server_address',
					required: true,
					label: _('Address of Active Directory domain controller or name of Active Directory domain')
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
				name: 'error-admember',
				headerText: _('AD Connection - An error occurred'),
				helpText: '<p>' + _('An error occurred during the join process of UCS into the Active Directory domain. The following information will give you some more details on which problems occurred during the join process.') + '</p>',
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					style: 'font-style:italic;',
					name: 'info',
					content: ''
				}]
			}, {
				'class': 'umc-adconnector-page-finished umc-adconnector-page',
				name: 'finished-admember',
				headerText: _('Completion of Active Directory Connection'),
				helpText: ' ',
				widgets: [{
					type: Text,
					name: 'help',
					content: _paragraph(
						_('The connection to the Active Directory domain has been configured successfully.'),
						_('It is necessary for already joined UCS systems to re-join the domain. This should be done via the UMC module <i>Domain join</i> separately on each system.')
					)
				}]
			}, {
				'class': 'umc-adconnector-page-credentials umc-adconnector-page',
				name: 'credentials-adconnector',
				headerText: _('Active Directory domain credentials'),
				helpText: ' ',
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'help',
					content: _('Enter the Active Directory domain information to establish the connection.')
				}, {
					type: TextBox,
					name: 'ad_server_address',
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
				'class': 'umc-adconnector-page-security umc-adconnector-page',
				name: 'ssl-adconnector',
				headerText: _('Security settings'),
				helpText: ' ',
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'info',
					content: _paragraph(
						_('An encrypted connection to the Active Directory domain could not be established. As a consequence authentication data is submitted in plaintext.'),
						_('To enable an encrypted connection, a certification authority needs to be configured on the Active Directory server. All steps necessary are described in the <a href="https://docs.software-univention.de/manual-%s.html#ad-connector:ad-zertifikat" target="_blank">UCS manual</a>.', version),
						_('After the certification authority has been set up, press <i>Next</i> to proceed.')
					)
				}]
			}, {
				'class': 'umc-adconnector-page-certificate umc-adconnector-page',
				name: 'certificate-adconnector',
				headerText: _('Upload AD root certificate'),
				helpText: ' ',
				widgets: [{
					type: Text,
					'class': 'umcPageHelpText',
					name: 'info',
					content: _('<p>To achieve a higher level of security, the Active Directory root certificate should be exported and uploaded here. The Active Directory certificate service creates that certificate. The necessary steps depend on the actual Microsoft Windows version and are described in the <a href="https://docs.software-univention.de/manual-%s.html#ad-connector:ad-zertifikat" target="_blank">UCS manual</a>. Alternatively, you may proceed without this configuration.</p>', version)

				}, {
					name: 'certificateUpload',
					type: Uploader,
					command: 'adconnector/upload/certificate',
					onUploadStarted: lang.hitch(this, function() {
						this.standby(true);
					}),
					onUploaded: lang.hitch(this, function(result) {
						this.standby(false);
						if (typeof result  == "string") {
							return;
						}
						if (result.success) {
							dialog.notify(_('The certificate was imported successfully'));
							this._next('certificate-adconnector'); // advance page
						} else {
							dialog.alert(_('Failed to import the certificate') + ': ' + result.message);
						}
					})
				}]
			}, {
				'class': 'umc-adconnector-page-syncconfig umc-adconnector-page',
				name: 'config-adconnector',
				headerText: _('Configuration of Active Directory domain synchronisation'),
				helpText: ' ',
				widgets: [{
					type: Text,
					name: 'info',
					content: ''
				}, {
					type: Text,
					'class': 'umcPageHelpText',
					name: 'help',
					content: '<p>' + _('Select the synchronisation direction between the UCS domain and the given Active Directory domain.') + '</p>'
				}, {
					type: RadioButtons,
					name: 'connectormode',
					staticValues: [{
						id: 'read',
						label: _('Unidirectional synchronisation of Active Directory to UCS.')
					}, {
						id: 'write',
						label: _('Unidirectional synchronisation of UCS to Active Directory.')
					}, {
						id: 'sync',
						label: _('Bidirectional synchronisation of UCS and Active Directory.')
					}],
					onChange: lang.hitch(this, function(value) {
						var map2img = {
							'default': '',
							read: '-right',
							write: '-left',
							sync: '-left-right'
						};
						var connectormode = this.getWidget('config-adconnector', 'connectormode').get('value');
						var page = this.getPage('config-adconnector');
						tools.forIn(map2img, lang.hitch(this, function(ikey, ival) {
							var cssClass = 'umc-adconnector-page-syncconfig' + ival;
							var useClass = connectormode == ikey;
							domClass.toggle(page.domNode, cssClass, useClass);
						}));
					})
				}]
			}, {
				'class': 'umc-adconnector-page-finished umc-adconnector-page',
				name: 'finished-adconnector',
				headerText: _('Completion of Active Directory Connection'),
				helpText: ' ',
				widgets: [{
					type: Text,
					name: 'help',
					content: _paragraph(
						_('The synchronisation of Univention Corporate Server and Active Directory has been successfully initiated.'),
						_('The UCS server is now ready for usage, and domain account data is now available.')
					)
				}]
			}];
		},

		_setupFooterButtons: function() {
			// change labels of footer buttons on particular pages
			var buttons = this.getPage('credentials-admember')._footerButtons;
			buttons.next.set('label', _('Join AD domain'));
			buttons = this.getPage('error-admember')._footerButtons;
			buttons.next.set('label', _('Retry to join'));
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._progressBar = new ProgressBar({});
			this.own(this._progressBar);

			this._keepSessionAlive = new timing.Timer(1000 * 10);
			this._keepSessionAlive.onTick = lang.hitch(server, 'ping');

			this._setupFooterButtons();
		},

		startup: function() {
			this.inherited(arguments);

			// pre-select admember mode
			this.getWidget('start', 'mode').set('value', 'admember');
		},

		_isConnectorMode: function() {
			return this.getWidget('start', 'mode').get('value') == 'adconnector';
		},

		_isMemberMode: function() {
			return this.getWidget('start', 'mode').get('value') == 'admember';
		},

		_updateConfigADConnectorPage: function(info) {
			var fqdnParts = info.DC_DNS_Name.split(/\./g);
			info._hostname = fqdnParts.shift();
			var msg = '<p>' + _('The server <i>%(_hostname)s (%(DC_IP)s)</i> is used as Active Directory Domain Controller for the domain <i>%(Domain)s</i>.', info) + '</p>';
			this.getWidget('config-adconnector', 'info').set('content', msg);
		},

		_updateErrorPage: function(mode, message, warnings) {
			//TODO: handling of warnings
			message = message || '<p>' + _('An unexpected error occurred. More information about the cause of the error can be found in the log file /var/log/univention/management-console-module-adconnector.log. Please retry the join process after resolving any conflicting issues.') + '</p>';
			message = message.replace(/\n/g, '<br>');
			this.getWidget('error-' + mode, 'info').set('content', message);
		},

		_checkADDomain: function() {
			var vals = this._getCredentials();
			vals.mode = this._isMemberMode() ? 'admember' : 'adconnector';
			return this.standbyDuring(tools.umcpCommand('adconnector/check_domain', vals)).then(lang.hitch(this, function(response) {
				//this._updateConfirmADMemberPage(response.result);
				return response.result;
			}), function() {
				return null;
			});
		},

		_confirmUnsecureConnectionWithADDomain: function() {
			return dialog.confirm(_('<p>An encrypted connection to the Active Directory domain could still not be established.</p><p>Confirm if you want to proceed with an unsecure connection.</p>'), [{
				name: 'cancel',
				label: _('Cancel')
			}, {
				name: 'confirm',
				'default': true,
				label: _('Continue without encryption')
			}], _('Security warning')).then(function(response) {
				return response == 'confirm';
			});
		},

		adMemberJoin: function(values) {
			this.standby(false);
			this._progressBar.reset(_('Joining UCS into Active Directory domain'));
			var vals = this._getCredentials();
			var deferred = tools.umcpProgressCommand(this._progressBar, 'adconnector/admember/join', vals, false).then(lang.hitch(this, function(result) {
				if (!result.success) {
					this._updateErrorPage('admember', result.error, result.warnings);
					return false;
				}
				return true;
			}), lang.hitch(this, function(error) {
				// NOTE: an alert dialogue with the traceback is shown automatically
				this._updateErrorPage('admember');
				return true;
			}));
			this.standbyDuring(deferred, this._progressBar);
			return deferred;
		},

		adConnectorSaveValues: function(adDomainInfo) {
			var vals = this._getADConnectorValues(adDomainInfo);
			return this.standbyDuring(tools.umcpCommand('adconnector/adconnector/save', vals)).then(lang.hitch(this, function(response) {
				if (!response.result.success) {
					dialog.alert(response.result.message);
					return false;
				}
				return true;
			}), function(err) {
				// should not occur, in any case, the error message will be prompted to the user
				return false;
			});
		},

		adConnectorStart: function() {
			return this.standbyDuring(tools.umcpCommand('adconnector/service', {
				action: 'start'
			})).then(lang.hitch(this, function(response) {
				if (!response.result.success) {
					dialog.alert(response.result.message);
					return false;
				}
				return true;
			}), function(err) {
				// should not occur, in any case, the error message will be prompted to the user
				return false;
			});
		},

		_nextADMember: function(pageName) {
			if (pageName == 'credentials-admember') {
				return this._checkADDomain().then(lang.hitch(this, function(adDomainInfo) {
					if (!adDomainInfo) {
						// server error message is shown, stay on the same page
						return pageName;
					}

					// start join process
					return this.adMemberJoin().then(lang.hitch(this, function(success) {
						if (success) {
							this._keepSessionAlive.start(); // will be stopped via destroy method
							return 'finished-admember';
						}
						return 'error-admember';
					}));
				}));
			}
			if (pageName == 'error-admember') {
				// retry again
				return 'credentials-admember';
			}
		},

		_nextADConnector: function(pageName) {
			if (pageName == 'credentials-adconnector') {
					return this._checkADDomain().then(lang.hitch(this, function(adDomainInfo) {
						if (!adDomainInfo) {
							// an error occurred (message is shown automatically) -> stay on the same page
							return pageName;
						}
						this._updateConfigADConnectorPage(adDomainInfo);
						this._adDomainInfo = adDomainInfo; // save values for later usage

						if (!adDomainInfo.ssl_supported) {
							// SSL is not available -> show a warning page
							return 'ssl-adconnector';
						}

						// SSL is available -> go to certificate page
						return 'certificate-adconnector';
					}));
			}
			if (pageName == 'ssl-adconnector') {
				// check again for SSL status...
				return this._checkADDomain().then(lang.hitch(this, function(adDomainInfo) {
					if (!adDomainInfo) {
						// server error message is shown, stay on the same page
						return pageName;
					}
					if (!adDomainInfo.ssl_supported) {
						return this._confirmUnsecureConnectionWithADDomain().then(function(confirmed) {
							if (confirmed) {
								// really no SSL! -> go to config page directly
								return 'config-adconnector';
							}

							// dialog has been canceled -> stay on the same page
							return pageName;
						});
					}

					// SSL is available now :) -> show certificate page
					return 'certificate-adconnector';
				}));
			}
			if (pageName == 'certificate-adconnector') {
				return 'config-adconnector';
			}
			if (pageName == 'config-adconnector') {
				return this.adConnectorSaveValues(this._adDomainInfo).then(lang.hitch(this, function(success) {
						if (success) {
							this.adConnectorStart();
							return 'finished-adconnector';
						} else {
							return pageName;
						}
				}));
			}
		},

		isPageVisible: function(pageName) {
			var isConnectorPage = pageName.indexOf('-adconnector') >= 0;
			if (isConnectorPage && !this._isConnectorMode()) {
				return false;
			}
			var isMemberPage = pageName.indexOf('-admember') >= 0;
			if (isMemberPage && !this._isMemberMode()) {
				return false;
			}
			return true;
		},

		next: function(pageName) {
			var nextPage = this.inherited(arguments);
			topic.publish('/umc/actions', 'adconnector', 'wizard', pageName, 'next');
			if (pageName == 'start') {
				return nextPage;
			}
			if (this._isMemberMode()) {
				return this._nextADMember(pageName);
			}
			if (this._isConnectorMode()) {
				return this._nextADConnector(pageName);
			}
			return nextPage;
		},

		previous: function(pageName) {
			topic.publish('/umc/actions', 'adconnector', 'wizard', pageName, 'previous');
			return this.inherited(arguments);
		},

		hasNext: function(pageName) {
			return pageName.indexOf('finished') < 0;
		},

		hasPrevious: function(pageName) {
			if (pageName == 'error-admember') {
				return false;
			}
			return pageName.indexOf('finished') < 0;
		},

		canCancel: function(pageName) {
			return pageName.indexOf('finished') < 0;
		},

		_finish: function(/*String*/ pageName) {
			if (pageName.indexOf('finished') < 0) {
				return;
			}

			if (this._isMemberMode()) {
				server.askRestart(_('Please confirm to carry out a restart of the UMC server components.')).then(
					lang.hitch(this, 'onFinished', 'admember'),
					lang.hitch(this, 'onFinished', 'admember')
				);
			} else {
				this.onFinished('adconnector');
			}
		},

		_gatherVisibleValues: function(pageName) {
			// collect values from visible pages and visible widgets
			var _vals = {};
			array.forEach(this.pages, function(ipageConf) {
				var matchesPageName = !pageName || ipageConf.name.indexOf(pageName) >= 0;
				if (this.isPageVisible(ipageConf.name) && matchesPageName) {
					var ipage = this.getPage(ipageConf.name);
					if (!ipage || !ipage._form) {
						return;
					}
					lang.mixin(_vals, ipage._form.get('value'));
				}
			}, this);
			return _vals;
		},

		_getCredentials: function() {
			return this._gatherVisibleValues('credentials');
		},

		_getADConnectorValues: function(adDomainInfo) {
			var vals = lang.mixin(this._gatherVisibleValues(), adDomainInfo);
			return {
				Host_IP: vals.DC_IP,
				LDAP_Host: vals.DC_DNS_Name,
				LDAP_Base: vals.LDAP_Base,
				LDAP_BindDN: vals.LDAP_BindDN,
				LDAP_Password: vals.password,
				KerberosDomain: vals.Domain,
				MappingSyncMode: vals.connectormode
			};
		},

		getValues: function() {
			// unused in this wizard, overwrite inherited method to return an empty dict
			return {};
		},

		destroy: function() {
			if (this._keepSessionAlive.isRunning) {
				this._keepSessionAlive.stop();
			}
			this.inherited(arguments);
		},

		'goto': function(idx) {
			var nextPage = this.pages[idx].name;
			this._updateButtons(nextPage);
			var page = this._pages[nextPage];
			this.selectChild(page);
		}

	});
});
