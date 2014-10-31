/*
 * Copyright 2013-2014 Univention GmbH
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
/*global define,window*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"umc/tools",
	"umc/dialog",
	"umc/render",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Text",
	"umc/widgets/TextArea",
	"umc/widgets/Button",
	"umc/widgets/Uploader",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, domClass, tools, dialog, render, ContainerWidget, ConfirmDialog, StandbyMixin, Text, TextArea, Button, Uploader, _) {

	return declare('umc.modules.udm.LicenseImportDialog', [ConfirmDialog, StandbyMixin], {
		// summary:
		//		Class that provides the license import Dialog for UCS. It support importing a new license.

		// umcPopup for content styling; umcConfirmDialog for max-width
		'class': 'umcPopup umcConfirmDialog umcUdmLicenseImportDialog',

		closable: true,
		options: [],

		_widgets: null,

		title: _('UCS license import'),

		postMixInProperties: function() {
			this.inherited(arguments);

			// add icon container
			this.message = new ContainerWidget({});
			this.message.addChild(new Text({
				'class': 'umcUDMLicenseImportIcon col-xxs-12 col-xs-4',
				content : ''
			}));

			// add main content
			this._widgets = render.widgets([{
				type: Text,
				name: 'message',
				content: '<p>' + _('New licenses that have been received after the activation of UCS or after a license purchase can be imported below. The license information can either be uploaded directly as file or it can be imported via copy and paste into the text field.') + '</p>'
			}, {
				type : TextArea,
				name : 'licenseText',
				style: 'width: 100%'
			}, {
				type : Uploader,
				name : 'licenseUpload',
				buttonLabel: _('Import from file...'),
				command: 'udm/license/import',
				onUploaded: lang.hitch(this, function(result) {
					if (typeof result == "string") {
						// Apache gateway timeout error (?)
						return;
					}
					this._handleUploaded(result);
				})
			}]);

			var buttons = [{
				name : 'btnLicenseText',
				label : _('Import from text field'),
				callback: lang.hitch(this, function() {
					var license = this._widgets.licenseText.get('value');
					this.standbyDuring(tools.umcpCommand('udm/license/import', { 'license': license }).then(
						lang.hitch(this, function(response) {
							this._handleUploaded(response.result[0]);
						})
					));
				})
			}, {
				name: 'submit', // workaround for a style as default button
				style: 'float: right',
				label: _('Close'),
				callback: lang.hitch(this, function() {
					this.close();
				})
			}];

			var content = render.layout([
				'titleImport',
				'message',
				'licenseUpload',
				'licenseText',
				['btnLicenseText', 'submit']
			], this._widgets, render.buttons(buttons));
			domClass.add(content.domNode, 'col-xxs-12 col-xs-8');
			this.message.addChild(content);
		},

		_handleUploaded: function(result) {
			if (result.success) {
				var btns = [{
					name: 'relogin',
					label: _('Logout'),
					'default': true,
					callback: function() {
						tools.closeSession();
						window.location.reload();
					}
				}, {
					name: 'cancel',
					label: _('Cancel'),
					callback: lang.hitch(this, function() {
						this.hide();
					})
				}];
				dialog.confirm(_('The license has been imported successfully.') + '<br>' + _('Please login again to complete the import process.'), btns);
			} else {
				var msg = _('The import of the license failed. Check the integrity of the original file given to you. If this error persists, please contact Univention or your Univention partner.');
				if (result.message) {
					msg = '<p>' + msg + '</p><p>' + _('Server error message:') + '</p><p class="umcServerErrorMessage">' + result.message + '</p>';
				}
				dialog.alert(msg);
			}
		}
	});
});

