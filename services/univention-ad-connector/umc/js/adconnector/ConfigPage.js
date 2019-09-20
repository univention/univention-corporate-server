/*
 * Copyright 2011-2019 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/when",
	"umc/dialog",
	"umc/tools",
	"umc/render",
	"umc/widgets/Page",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Text",
	"umc/widgets/InfoUploader",
	"umc/i18n!umc/modules/adconnector"
], function(declare, lang, array, when, dialog, tools, render, Page, StandbyMixin, Text, InfoUploader,  _) {

	var makeParagraphs = function(sentences) {
		return array.map(sentences, function(para) {
			return '<p>' + para + '</p>';
		}).join('');
	};

	return declare("umc.modules.adconnector.ConfigPage", [Page, StandbyMixin], {
		initialState: null,

		headerText: _('Configuration of the Active Directory connection'),

		_widgets: null,

		_buttons: null,

		postCreate: function() {
			this.inherited(arguments);
			this._setHelpText(this.initialState);
		},

		_setHelpText: function(state) {
			if (state && state.mode_admember) {
				this.helpText = _('The system is part of an Active Directory domain.');
			} else if (state && state.mode_adconnector) {
				this.helpText = _('The UCS domain exists in parallel to an Active Directory domain.');
			}
			this.helpText += ' ' + _('This module configures the connection between the Univention Corporate Server and Active Directory.');
			this.set('helpText', this.helpText);
		},

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				name: 'running',
				type: Text
			}, {
				name: 'unencryptedActivateSSL',
				type: Text,
				content: '<p style="margin-top: 4em;">' +
					_('It is also possible to just activate the encrypted connection without certificate verification.') +
					'</p>'
			}, {
				name: 'certificateUpload',
				type: InfoUploader,
				showClearButton: false,
				command: 'adconnector/upload/certificate',
				onUploaded: lang.hitch(this, function(result) {
					if (typeof result  == "string") {
						return;
					}
					if (result.success) {
						this.addNotification(_('The certificate was imported successfully'));
					} else {
						dialog.alert(_('Failed to import the certificate') + ': ' + result.message);
					}
					this.showHideElements();
				})
			}, {
				name: 'pwdsyncInfoADMember',
				type: Text,
				content: makeParagraphs([
					_('By default the Active Directory connection does not transfer encrypted password data into the UCS directory service. The system uses the Active Directory Kerberos infrastructure for authentication.'),
					_('However, in some scenarios it may be reasonable to transfer encrypted password hashes. Please refer the UCS manual in order to activate the password synchronization.')
				])
			}];

			var buttons = [{
				name: 'start',
				label: _('Start Active Directory connection service'),
				callback: lang.hitch(this, '_umcpCommandAndUpdate', 'adconnector/service', {action: 'start'})
			}, {
				name: 'stop',
				label: _('Stop Active Directory connection service'),
				callback: lang.hitch(this, '_umcpCommandAndUpdate', 'adconnector/service', {action: 'stop'})
			}, {
				name: 'activate',
				label: _('Activate encrypted connection'),
				callback: lang.hitch(this, '_umcpCommandAndUpdate', 'adconnector/enable_ssl')
//			}, {
//				name: 'password_sync',
//				label: _('Activate password synchronization'),
//				callback: lang.hitch(this, '_umcpCommandAndUpdate', 'adconnector/password_sync_service')
//			}, {
//				name: 'password_sync_stop',
//				label: _('Stop password synchronization'),
//				callback: lang.hitch(this, '_umcpCommandAndUpdate', 'adconnector/password_sync_service', {enable: false})
			}];

			this._widgets = render.widgets(widgets);
			this._buttons = render.buttons(buttons);

			var layout = [{
				label: _('Active Directory connection service'),
				layout: ['running', 'start', 'stop']
			}, {
				label: _('Active Directory connection SSL configuration'),
				layout: ['certificateUpload', 'unencryptedActivateSSL', 'activate']
			}];
			if (this.initialState.mode_admember) {
				layout.push({
					label: _('Password sync'),
					layout: ['pwdsyncInfoADMember']
				});
			}
			var _container = render.layout(layout, this._widgets, this._buttons);

			_container.set('style', 'overflow: auto');
			this.addChild(_container);

			this.showHideElements(this.initialState);
		},

		_umcpCommandAndUpdate: function(command, params) {
			return this.standbyDuring(tools.umcpCommand(command, params).then(lang.hitch(this, function() {
				this.showHideElements();
			})));
		},

		showHideElements: function(state) {
			if (!state) {
				state = this.standbyDuring(tools.umcpCommand('adconnector/state')).then(function(response) {
					return response.result;
				});
			}
			when(state, lang.hitch(this, function(state) {
				this._setHelpText(state);

				if (state.running) {
					this._widgets.running.set('content', _('Active Directory connection service is currently running.'));
					this._buttons.start.set('visible', false);
					this._buttons.stop.set('visible', true);
				} else {
					var message = _('Active Directory connection service is not running.');
					this._buttons.start.set('visible', true);
					this._buttons.stop.set('visible', false);
					this._widgets.running.set('content', message);
				}
				var certMsg = '';
				var showEnableSSL = false;
				if (!state.certificate) {
					var version = tools.status('ucsVersion').split('-')[0];
					if (!state.ssl_enabled) {
						showEnableSSL = state.mode_adconnector;
						certMsg = makeParagraphs([
							_('Currently, an unencrypted connection to the Active Directory domain is used.'),
							_('To achieve a higher level of security, the Active Directory root certificate should be exported and uploaded here. The Active Directory certificate service creates that certificate.'),
							_('The necessary steps depend on the actual Microsoft Windows version and are described in the <a href="https://docs.software-univention.de/manual-%s.html#ad-connector:ad-zertifikat" target="_blank">UCS manual</a>.', version)
						]);
					} else {
						certMsg = makeParagraphs([
							_('Currently, an encrypted connection between UCS and the Active Directory domain is used.'),
							_('To achieve a higher level of security, the Active Directory root certificate should be exported and uploaded here. The Active Directory certificate service creates that certificate.'),
							_('The necessary steps depend on the actual Microsoft Windows version and are described in the <a href="https://docs.software-univention.de/manual-%s.html#ad-connector:ad-zertifikat" target="_blank">UCS manual</a>.', version)
						]);
					}
				} else {
					certMsg = makeParagraphs([
						_('Currently, a secured connection between UCS and the Active Directory domain is used.'),
						_('If there is a need for adjustment, you may upload a new root certificate of the Active Directory domain.')
					]);
				}
				this._widgets.certificateUpload.set('value', certMsg);

				this._widgets.unencryptedActivateSSL.set('visible', showEnableSSL);
				this._buttons.activate.set('visible', showEnableSSL);

				this._widgets.pwdsyncInfoADMember.set('visible', state.mode_admember);
//				this._buttons.password_sync.set('visible', state.mode_admember && !state.password_sync_enabled);
//				this._buttons.password_sync_stop.set('visible', state.mode_admember && state.password_sync_enabled);
			}));
		}
	});

});
