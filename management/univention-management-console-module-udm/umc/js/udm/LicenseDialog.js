/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Text",
	"umc/widgets/TitlePane",
	"umc/widgets/ContainerWidget",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, domClass, tools, dialog, ConfirmDialog, StandbyMixin, Text, TitlePane, ContainerWidget, _) {

	return declare('umc.modules.udm.LicenseDialog', [ConfirmDialog, StandbyMixin], {
		// summary:
		//		Class that provides the license Dialog for UCS. It shows details about the current license.

		'class': 'umcUdmLicenseDialog umcLargeDialog',

		_iconWidget: null,
		_messageWidget: null,
		_additionalInfoWidget: null,

		licenseInfo: null,

		standbyOpacity: 1.0,
		closable: true,

		postMixInProperties: function() {
			this.inherited(arguments);

			this.title = _('Information about the current UCS license');

			this.options = [{
				name: 'close',
				label: _('Close'),
				'default': true,
				callback: lang.hitch(this, function() {
					this.close();
				})
			}];

			this._iconWidget = new Text({
				'class': 'umcUDMLicenseIcon col-xxs-12 col-xs-4',
				content : ''
			});
			this._messageWidget = new Text({
				'class': 'col-xxs-12 col-xs-8',
				content : ''
			});

			this._additionalInfoWidget = new Text({
				'class': 'col-xxs-12',
				content : ''
			});

			this.message = new ContainerWidget({});
			this.message.addChild(this._iconWidget);
			this.message.addChild(this._messageWidget);
			this.message.addChild(this._additionalInfoWidget);

			this.updateLicense();
		},

		updateLicense: function() {
			this.standbyDuring(tools.umcpCommand('udm/license/info').then(lang.hitch(this, function(response) {
				this.licenseInfo = response.result;
				this.showLicense();
			}), lang.hitch(this, function() {
				dialog.alert(_('Updating the license information has failed'));
			})));
		},

		showLicense: function() {
			if (!this.licenseInfo) {
				return;
			}

			var entries = {};
				// content: license info and upload widgets
				var product = '';
				if (this.licenseInfo.oemProductTypes.length === 0) {
					product = this.licenseInfo.licenseTypes.join(', ');
				} else {
					product = this.licenseInfo.oemProductTypes.join(', ');
				}

				var additionalInfo = {
					'core': _('Information about the <a href="https://www.univention.com/downloads/license-models/ucs-core-edition" target="_blank">terms of use</a> for this free license can be found on the Univention website. Information about the <a href="https://www.univention.com/enterprise-subscriptions" target="_blank">UCS Enterprise Subscriptions</a> can also be found there.'),
					'': ''
				}[this.licenseInfo.freeLicense];
				this._additionalInfoWidget.set('content', additionalInfo);

				var licenseTypeLabel = {
					'core': 'UCS Core Edition',
					'': _('UCS License')
				}[this.licenseInfo.freeLicense];

					// subtract system accounts
					if (this.licenseInfo.real.users >= this.licenseInfo.sysAccountsFound) {
						this.licenseInfo.real.users -= this.licenseInfo.sysAccountsFound;
					}

					entries = [
						[_('License type'), licenseTypeLabel],
						[_('LDAP base'), this.licenseInfo.baseDN],
						// [_('Servers'), this._limitInfo('servers')], // Do not show server count. See Bug #45944
						[_('User accounts'), this._limitInfo('users')],
						[_('Managed Clients'), this._limitInfo('managedclients')],
						[_('Key ID'), this.licenseInfo.keyID],
						[_('Expiry date'), _(this.licenseInfo.endDate)],
						[_('Valid product types'), product]
					];

			// render information
			var html = array.map(entries, function(ientry) {
				if (ientry.length == 1) {
					return lang.replace('<p>{0}<p>', ientry);
				}
				return lang.replace('<p><b>{0}:</b>&nbsp;&nbsp;{1}</p>', ientry);
			}).join('\n');
			this._messageWidget.set('content', html);

			// show and recenter dialog
			this.show().then(lang.hitch(this, function() {
				this._position();
			}));
		},

		_limitInfo: function(limit) {
			if (this.licenseInfo.licenses[limit] === null) {
				return  _('unlimited');
			} else {
				return _('%(limit)s (used: %(used)s)', {limit: this.licenseInfo.licenses[limit], used: this.licenseInfo.real[limit]});
			}
		}
	});
});

