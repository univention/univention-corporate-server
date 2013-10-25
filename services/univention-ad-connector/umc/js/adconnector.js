/*
 * Copyright 2011-2013 Univention GmbH
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
/*global define window*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dijit/Dialog",
	"umc/dialog",
	"umc/tools",
	"umc/render",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/Wizard",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/widgets/TextBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/PasswordBox",
	"umc/widgets/InfoUploader",
	"umc/i18n!umc/modules/adconnector"
], function(declare, lang, array, DijitDialog, dialog, tools, render, Module, Page, Wizard, StandbyMixin, Text, Button, TextBox, CheckBox, ComboBox, PasswordBox, InfoUploader, _) {

	var ADConnectorWizard = declare("umc.modules._adconnector.Wizard", [Wizard], {
		pages: null,

		variables: null,

		addNotification: dialog.notify,

		constructor: function() {
			this.pages = [{
				name: 'fqdn',
				helpText: '<p>' + _('Please enter the fully qualified hostname of the Active Directory server.') + '</p><p>'
					+ _('The hostname must be resolvable by the UCS server. A DNS entry can be configured in the DNS module, or a static host record can be configured through the Univention Configuration Registry module, e.g.')
					+ '</p><p>hosts/static/192.168.0.10=w2k8-ad.example.com</p>',
				headerText: _('UCS Active Directory Connector configuration'),
				widgets: [{
					name: 'LDAP_Host',
					type: TextBox,
					required: true,
					regExp: '.+',
					invalidMessage: _('The hostname of the Active Directory server is required'),
					label: _('Active Directory Server')
				}, {
					name: 'guess',
					type: CheckBox,
					label: _('Automatic determination of the LDAP configuration')
				}],
				layout: ['LDAP_Host', 'guess']
			}, {
				name: 'ldap',
				helpText: _('LDAP und kerberos configuration of the Active Directory server needs to be specified for the synchronisation'),
				headerText: _('LDAP and Kerberos'),
				widgets: [{
					name: 'LDAP_Base',
					type: TextBox,
					required: true,
					sizeClass: 'OneAndAHalf',
					label: _('LDAP base')
				}, {
					name: 'LDAP_BindDN',
					required: true,
					type: TextBox,
					sizeClass: 'OneAndAHalf',
					label: _('LDAP DN of the synchronisation user')
				}, {
					name: 'LDAP_Password',
					type: PasswordBox,
					label: _('Password of the synchronisation user')
				}, {
					name: 'KerberosDomain',
					type: TextBox,
					label: _('Kerberos domain')
				}],
				layout: ['LDAP_Base', 'LDAP_BindDN', 'LDAP_Password', 'KerberosDomain']
			}, {
				name: 'sync',
				helpText: _('UCS Active Directory Connector supports three types of synchronisation.'),
				headerText: _('Synchronisation mode'),
				widgets: [{
					name: 'MappingSyncMode',
					type: ComboBox,
					staticValues: [
						{
							id: 'sync',
							label: 'AD <-> UCS'
						},{
							id: 'read',
							label: 'AD -> UCS'
						}, {
							id: 'write',
							label: 'UCS -> AD'
						}],
					label: _('Synchronisation mode')
				}, {
					name: 'MappingGroupLanguage',
					label: _('System language of Active Directory server'),
					type: ComboBox,
					staticValues: [
						{
							id: 'de',
							label: _('German')
						}, {
							id: 'en',
							label: _('English')
						}]
				}],
				layout: ['MappingSyncMode', 'MappingGroupLanguage']
			}, {
				name: 'extended',
				helpText: _('The following settings control the internal behaviour of the UCS Active Directory connector. For all attributes reasonable default values are provided.'),
				headerText: _('Extended settings'),
				widgets: [{
					name: 'PollSleep',
					type: TextBox,
					sizeClass: 'OneThird',
					label: _('Poll Interval (seconds)')
				}, {
					name: 'RetryRejected',
					label: _('Retry interval for rejected objects'),
					type: TextBox,
					sizeClass: 'OneThird'
				}, {
					name: 'DebugLevel',
					label: _('Debug level of Active Directory Connector'),
					type: TextBox,
					sizeClass: 'OneThird'
				}, {
					name: 'DebugFunction',
					label: _('Add debug output for functions'),
					type: CheckBox,
					sizeClass: 'OneThird'
				}],
				layout: ['PollSleep', 'RetryRejected', 'DebugLevel', 'DebugFunction']
			}];
		},

		next: function(/*String*/ currentID) {
			if (!currentID) {
				tools.forIn(this.variables, lang.hitch(this, function(option, value) {
					var w = this.getWidget(null, option);
					if (w) {
						w.set('value', value);
					}
				}));
				// of no LDAP_base is set activate the automatic determination
				if (!this.variables.LDAP_base) {
					this.getWidget('fqdn', 'guess').set('value', true);
				}
			} else if (currentID == 'fqdn') {
				var nameWidget = this.getWidget('LDAP_Host');
				if (!nameWidget.isValid()) {
					nameWidget.focus();
					return null;
				}

				var guess = this.getWidget('fqdn', 'guess');
				if (guess.get('value')) {
					this.standby(true);
					var server = this.getWidget('fqdn', 'LDAP_Host');
					tools.umcpCommand('adconnector/guess', { 'LDAP_Host' : server.get('value') }).then(lang.hitch(this, function(response) {
						if (response.result.LDAP_Base) {
							this.getWidget('ldap', 'LDAP_Base').set('value', response.result.LDAP_Base);
							this.getWidget('ldap', 'LDAP_BindDN').set('value', 'cn=Administrator,cn=users,' + response.result.LDAP_Base);
							this.getWidget('ldap', 'KerberosDomain').set('value', tools.explodeDn(response.result.LDAP_Base, true).join('.'));
						} else {
							this.addNotification(response.result.message);
						}
						this.standby(false);
					}));
				}
			} else if (currentID == 'ldap') {
				var valid = true;
				array.forEach(['LDAP_Base', 'LDAP_BindDN', 'LDAP_Password'], lang.hitch(this, function(widgetName) {
					if (!this.getWidget(widgetName).isValid()) {
						this.getWidget(widgetName).focus();
						valid = false;
						return false;
					}
				}));
				if (!valid) {
					return null;
				}

				var password = this.getWidget('ldap', 'LDAP_Password');
				if (!this.variables.passwordExists && !password.get('value')) {
					dialog.alert(_('The password for the synchronisation account is required!'));
					return currentID;
				}
			}

			return this.inherited(arguments);
		},

		onFinished: function(values) {
			this.standby(true);
			tools.umcpCommand('adconnector/save', values).then(lang.hitch(this, function(response) {
				if (!response.result.success) {
					dialog.alert(response.result.message);
				} else {
					this.addNotification(response.result.message);
				}
				this.standby(false);
			}));
		}
	});

	var ADConnectorWizardDialog = declare("umc.modules._adconnector.WizardDialog", [DijitDialog, StandbyMixin], {
		// summary:
		//		Dialog class for the configuration wizard

		'class' : 'umcPopup',

		_wizard: null,

		addNotification: dialog.notify,

		buildRendering: function() {
			this.inherited(arguments);

			tools.umcpCommand('adconnector/load').then(lang.hitch(this, function(response) {
				this._wizard = new ADConnectorWizard({
					style: 'width: 500px; height: 400px;',
					variables: response.result,
					addNotification: lang.hitch(this, 'addNotification')
				});
				this.set('content', this._wizard);
				this._wizard.on('Finished', lang.hitch(this, function() {
					this.onSaved();
				}));
				this._wizard.on('Cancel', lang.hitch(this, function() {
					this.hide();
					this.destroyRecursive();
				}));
				this._wizard.startup();
			}));
		},

		onSaved: function() {
		}
	});

	return declare("umc.modules.adconnector", [Module], {

		standbyOpacity: 1.00,

		_widgets: null,

		_buttons: null,

		_page: null,

		buildRendering: function() {
			this.inherited(arguments);

			this._page = new Page({
				helpText: _("This module provides a configuration wizard for the UCS Active Directory Connector to simplify the setup."),
				headerText: _("Configuration of the UCS Active Directory Connector")
			});
			this.addChild(this._page);

			var widgets = [{
				name: 'configured',
				type: Text
			}, {
				name: 'running',
				type: Text
			}, {
				name: 'certificateUpload',
				type: InfoUploader,
				showClearButton: false,
				command: 'adconnector/upload/certificate',
				onUploaded: lang.hitch(this, function(result) {
					if (typeof  result  == "string") {
						return;
					}
					if (result.success) {
						this.addNotification(_('The certificate was imported successfully'));
						this.showHideElements();
					} else {
						dialog.alert(_('Failed to import the certificate') + ': ' + result.message);
					}
				})
			}, {
				name: 'download',
				type: Text,
				content: ''
			}];

			var buttons = [{
				name: 'start',
				label: _('Start UCS Active Directory Connector'),
				callback: lang.hitch(this, function() {
					tools.umcpCommand('adconnector/service', { action : 'start' }).then(lang.hitch(this, function(response) {
						this.showHideElements();
					}));
				})
			}, {
				name: 'stop',
				label: _('Stop UCS Active Directory Connector'),
				callback: lang.hitch(this, function() {
					tools.umcpCommand('adconnector/service', { action : 'stop' }).then(lang.hitch(this, function(response) {
						this.showHideElements();
					}));
				})
			}, {
				name: 'configure',
				label: _('Configure UCS Active Directory Connector'),
				callback: lang.hitch(this, function() {
					var dlg = new ADConnectorWizardDialog({
						title: _('UCS Active Directory Connector Wizard'),
						addNotification: lang.hitch(this, 'addNotification')
					});
					dlg.show();
					dlg.on('saved', lang.hitch(this, function() {
						dlg.destroyRecursive();
						this.showHideElements();
					}));
				})
			}];

			this._widgets = render.widgets(widgets);
			this._buttons = render.buttons(buttons);

			var _container = render.layout([{
				label: _('Configuration'),
				layout: ['configured',  'configure']
			}, {
				label: _('UCS Active Directory Connector service'),
				layout: ['running', 'start', 'stop']
			}, {
				label: _('Active Directory Server configuration'),
				layout: ['certificateUpload']
			}, {
				label: _('Download the password service for Windows and the UCS certificate'),
				layout: ['download']
			}], this._widgets, this._buttons);

			_container.set('style', 'overflow: auto');
			this._page.addChild(_container);

			this.showHideElements();
		},

		_update_download_text: function(result) {
			var downloadText = _('The MSI files are the installation files for the password service and can be started by double clicking on it.') + '<br>'
			+ _('The package is installed in the <b>C:\\Windows\\UCS-AD-Connector</b> directory automatically. Additionally, the password service is integrated into the Windows environment as a system service, which means the service can be started automatically or manually.')
			+ '<ul><li><a target="_blank" href="/univention-ad-connector/ucs-ad-connector.msi">ucs-ad-connector.msi</a><br>'
			+ _('Installation file for the password service for <b>%s</b> Windows.<br />It can be started by double clicking on it.', '32bit')
			+ '</li><li><a target="_blank" href="/univention-ad-connector/ucs-ad-connector-64bit.msi">ucs-ad-connector-64bit.msi</a><br>'
			+ _('Installation file for the password service for <b>%s</b> Windows.<br />It can be started by double clicking on it.', '64bit')
			+ '</li><li><a target="_blank" href="/univention-ad-connector/vcredist_x86.exe">vcredist_x86.exe</a><br>'
			+ _('Microsoft Visual C++ 2010 Redistributable Package (x86) - <b>Must</b> be installed on a <b>64bit</b> Windows.')
			+ '</li>';

			if (result.configured) {
				downloadText += '<li id="adconnector/cert.pem"><br>'
				+ _('The <b>cert.pem</b> file contains the SSL certificates created in UCS for secure communication.') + ' '
				+ _('It must be copied into the installation directory of the password service.')
				+ _('<br />Please verify that the file has been downloaded as <b>cert.pem</b>, Internet Explorer appends a .txt under some circumstances.')
				+ '</li><li id="adconnector/private.key"><br>'
				+ _('The <b>private.key</b> file contains the private key to the SSL certificates.') + ' '
				+ _('It must be copied into the installation directory of the password service.')
				+ '</li>';
			}
			downloadText += '</ul>';
			this._widgets.download.set('content', downloadText);

			if (result.configured) {
				this.placeButton('adconnector/private.key');
				this.placeButton('adconnector/cert.pem');
			}
		},

		placeButton: function(url) {
			var label = _('Download %s', url.substring(url.indexOf('/') + 1));
			var button = new Button({
				label: label,
				callback: function() {
					var remoteWin = window.open('', '_blank');
					tools.umcpCommand(url).then(function(response) {
						remoteWin.location = response.result;
					});
				}
			});
			this.own(button);
			button.placeAt(url, 'first');
		},

		showHideElements: function() {
			this.standbyDuring(tools.umcpCommand('adconnector/state').then(lang.hitch(this, function(response) {
				this._update_download_text(response.result);

				if (response.result.configured) {
					this._widgets.configured.set('content', _('The configuration process has been finished and all required settings for UCS Active Directory Connector are set.'));
				} else {
					this._widgets.configured.set('content', _('The configuration process has not been started yet or is incomplete.'));
				}
				if (!response.result.certificate) {
					this._widgets.certificateUpload.set('value', _('The Active Directory certificate has not been installed yet.'));
				} else {
					this._widgets.certificateUpload.set('value', _('The Active Directory certificate has been successfully installed.'));
				}
				if (response.result.running) {
					this._widgets.running.set('content', _('UCS Active Directory Connector is currently running.'));
					this._buttons.start.set('visible', false);
					this._buttons.stop.set('visible', true);
				} else {
					var message = _('UCS Active Directory Connector is not running.');
					if (!response.result.configured) {
						message += _(' The Configuation of UCS Active Directory Connector must be completed before the server can be started.');
						this._buttons.start.set('visible', false);
						this._buttons.stop.set('visible', false);
					} else {
						this._buttons.start.set('visible', true);
						this._buttons.stop.set('visible', false);
					}
					this._widgets.running.set('content', message);
				}
			})));
		}
	});

});
