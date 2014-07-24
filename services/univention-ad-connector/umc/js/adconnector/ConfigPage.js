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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/when",
	"dijit/Dialog",
	"umc/dialog",
	"umc/tools",
	"umc/render",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/Wizard",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/PasswordBox",
	"umc/widgets/InfoUploader",
	"umc/i18n!umc/modules/adconnector"
], function(declare, lang, array, when, DijitDialog, dialog, tools, render, Module, Page, Wizard, StandbyMixin, Text, TextBox, CheckBox, ComboBox, PasswordBox, InfoUploader, _) {

	return declare("umc.modules.adconnector.ConfigPage", Page, {
		initialState: null,

		helpText: _('This module provides a configuration wizard for the UCS Active Directory Connector to simplify the setup.'),
		headerText: _('Configuration of the UCS Active Directory Connector'),

		_widgets: null,

		_buttons: null,

		buildRendering: function() {
			this.inherited(arguments);

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
			this.addChild(_container);

			this.showHideElements(this.initialState);
		},

		_update_download_text: function(result) {
			var downloadText = _('The MSI files are the installation files for the password service and can be started by double clicking on it.') + '<br>'
			+ _('The package is installed in the <b>C:\\Windows\\UCS-AD-Connector</b> directory automatically. Additionally, the password service is integrated into the Windows environment as a system service, which means the service can be started automatically or manually.')
			+ '<ul><li><a href="/univention-ad-connector/ucs-ad-connector.msi">ucs-ad-connector.msi</a><br>'
			+ _('Installation file for the password service for <b>%s</b> Windows.<br />It can be started by double clicking on it.', '32bit')
			+ '</li><li><a href="/univention-ad-connector/ucs-ad-connector-64bit.msi">ucs-ad-connector-64bit.msi</a><br>'
			+ _('Installation file for the password service for <b>%s</b> Windows.<br />It can be started by double clicking on it.', '64bit')
			+ '</li><li><a href="/univention-ad-connector/vcredist_x86.exe">vcredist_x86.exe</a><br>'
			+ _('Microsoft Visual C++ 2010 Redistributable Package (x86) - <b>Must</b> be installed on a <b>64bit</b> Windows.')
			+ '</li>';

			if (result.configured) {
				downloadText += '<li><a href="/umcp/command/adconnector/cert.pem" type="application/octet-stream">cert.pem</a><br>'
				+ _('The <b>cert.pem</b> file contains the SSL certificates created in UCS for secure communication.') + ' '
				+ _('It must be copied into the installation directory of the password service.')
				+ _('<br />Please verify that the file has been downloaded as <b>cert.pem</b>, Internet Explorer appends a .txt under some circumstances.')
				+ '</li><li><a href="/umcp/command/adconnector/private.key" type="application/octet-stream">private.key</a><br>'
				+ _('The <b>private.key</b> file contains the private key to the SSL certificates.') + ' '
				+ _('It must be copied into the installation directory of the password service.')
				+ '</li>';
			}
			downloadText += '</ul>';
			this._widgets.download.set('content', downloadText);
		},

		showHideElements: function(state) {
			if (!state) {
				state = this.standbyDuring(tools.umcpCommand('adconnector/state')).then(function(response) {
					return response.result;
				});
			}
			when(state, lang.hitch(this, function(state) {
				this._update_download_text(state);

				if (state.configured) {
					this._widgets.configured.set('content', _('The configuration process has been finished and all required settings for UCS Active Directory Connector are set.'));
				} else {
					this._widgets.configured.set('content', _('The configuration process has not been started yet or is incomplete.'));
				}
				if (!state.certificate) {
					this._widgets.certificateUpload.set('value', _('The Active Directory certificate has not been installed yet.'));
				} else {
					this._widgets.certificateUpload.set('value', _('The Active Directory certificate has been successfully installed.'));
				}
				if (state.running) {
					this._widgets.running.set('content', _('UCS Active Directory Connector is currently running.'));
					this._buttons.start.set('visible', false);
					this._buttons.stop.set('visible', true);
				} else {
					var message = _('UCS Active Directory Connector is not running.');
					if (!state.configured) {
						message += _(' The Configuation of UCS Active Directory Connector must be completed before the server can be started.');
						this._buttons.start.set('visible', false);
						this._buttons.stop.set('visible', false);
					} else {
						this._buttons.start.set('visible', true);
						this._buttons.stop.set('visible', false);
					}
					this._widgets.running.set('content', message);
				}
			}));
		}
	});

});
