/*
 * Copyright 2011-2015 Univention GmbH
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
	"umc/tools",
	"umc/dialog",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Text",
	"umc/widgets/TitlePane",
	"umc/widgets/ContainerWidget",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, domClass, tools, dialog, ConfirmDialog, StandbyMixin, Text, TitlePane, ContainerWidget, _) {

	var ffpu_license_info = _('<p>The "free for personal use" edition of Univention Corporate Server is a special software license which allows users free use of the Univention Corporate Server and software products based on it for private purposes acc. to § 13 BGB (German Civil Code).</p><p>In the scope of this license, UCS can be downloaded, installed and used from our servers. It is, however, not permitted to make the software available to third parties to download or use it in the scope of a predominantly professional or commercial usage.</p><p>The license of the "free for personal use" edition of UCS occurs in the scope of a gift contract. We thus exclude all warranty and liability claims, except in the case of deliberate intention or gross negligence. We emphasise that the liability, warranty, support and maintance claims arising from our commercial software contracts do not apply to the "free for personal use" edition.</p><p>We wish you a lot of happiness using the "free for personal use" edition of Univention Corporate Server and look forward to receiving your feedback. If you have any questions, please consult our forum, which can be found on the Internet at http://forum.univention.de/.</p>');

	return declare('umc.modules.udm.LicenseDialog', [ConfirmDialog, StandbyMixin], {
		// summary:
		//		Class that provides the license Dialog for UCS. It shows details about the current license.

		// umcPopup for content styling; umcConfirmDialog for max-width
		'class': 'umcPopup umcConfirmDialog umcUdmLicenseDialog umcLargeDialog',

		_iconWidget: null,
		_messageWidget: null,
		_ffpuTextWidget: null,
		_ffpuTitlePane: null,

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
			this._ffpuTitlePane = new TitlePane({
				'class': 'umcUDMLicenseTitlePane col-xs-12 dijitHidden',
				open: false,
				title: _('Information about the "free for personal use" license'),
				_setVisibleAttr: lang.hitch(this, function(visible) {
					if (this._ffpuTitlePane) {
						domClass.toggle(this._ffpuTitlePane.domNode, 'dijitHidden', !visible);
					}
				})
			});

			this.message = new ContainerWidget({});
			this.message.addChild(this._iconWidget);
			this.message.addChild(this._messageWidget);
			this.message.addChild(this._ffpuTitlePane);

			this._ffpuTextWidget = new Text({'content': ''});
			this._ffpuTitlePane.addChild(this._ffpuTextWidget);

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

			var isFFPU = this.licenseInfo.ffpu;
			this._ffpuTitlePane.set('visible', isFFPU);

			var entries = {};
			if (this.licenseInfo.licenseVersion === 'gpl') {
				entries = [
					[_('License type'), _('GPL')],
					[_('You are using a GPL license which is not eligible for maintenance or support claims.')]
				];
			} else {

				// content: license info and upload widgets
				var product = '';
				if (this.licenseInfo.oemProductTypes.length === 0) {
					product = this.licenseInfo.licenseTypes.join(', ');
				} else {
					product = this.licenseInfo.oemProductTypes.join(', ');
				}

				if (this.licenseInfo.licenseVersion === '1') {

					// substract system accounts
					if (this.licenseInfo.real.account >= this.licenseInfo.sysAccountsFound) {
						this.licenseInfo.real.account -= this.licenseInfo.sysAccountsFound;
					}

					entries = [
						[_('License type'),	this.licenseInfo.ffpu ? 'Free for personal use edition' : _('UCS License')],
						[_('LDAP base'), this.licenseInfo.baseDN],
						[_('User accounts'), this._limitInfo('account')],
						[_('Clients'), this._limitInfo('client')],
						[_('Desktops'), this._limitInfo('desktop')],
						[_('Expiry date'), _(this.licenseInfo.endDate)],
						[_('Valid product types'), product]
					];


				} else if (this.licenseInfo.licenseVersion === '2') {

					// substract system accounts
					if (this.licenseInfo.real.users >= this.licenseInfo.sysAccountsFound) {
						this.licenseInfo.real.users -= this.licenseInfo.sysAccountsFound;
					}

					entries = [
						[_('License type'), this.licenseInfo.ffpu ? 'Free for personal use edition' : _('UCS License')],
						[_('LDAP base'), this.licenseInfo.baseDN],
						[_('Servers'), this._limitInfo('servers')],
						[_('User accounts'), this._limitInfo('users')],
						[_('Managed Clients'), this._limitInfo('managedclients')],
						[_('Corporate Clients'), this._limitInfo('corporateclients')],
						[_('DVS Users'), this._limitInfo('virtualdesktopusers')],
						[_('DVS Clients'), this._limitInfo('virtualdesktopclients')],
						[_('Servers with standard support'), this.licenseInfo.support],
						[_('Servers with premium support'), this.licenseInfo.premiumSupport],
						[_('Key ID'), this.licenseInfo.keyID],
						[_('Expiry date'), _(this.licenseInfo.endDate)],
						[_('Valid product types'), product]
					];
				}

				this._ffpuTextWidget.set('content', isFFPU ? ffpu_license_info : '');
			}

			// render information
			var html = array.map(entries, function(ientry) {
				if (ientry.length == 1) {
					return lang.replace('<p>{0}<p>', ientry);
				}
				return lang.replace('<p><b>{0}:</b>&nbsp;&nbsp;{1}</p>', ientry);
			}).join('\n');
			this._messageWidget.set('content', html);

			// show and recenter dialog
			this.show().then(lang.hitch(this, function() {;
				this._position();
			}));
		},

		_limitInfo: function(limit) {
			if (this.licenseInfo.licenses[limit] === null) {
				return  _('unlimited');
			} else {
				return _('%s (used: %s)', this.licenseInfo.licenses[limit], this.licenseInfo.real[limit]);
			}
		}
	});
});

