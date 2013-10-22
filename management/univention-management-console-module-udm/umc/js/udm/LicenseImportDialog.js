/*
 * Copyright 2013 Univention GmbH
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
	"umc/tools",
	"umc/dialog",
	"umc/render",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Text",
	"umc/widgets/TextArea",
	"umc/widgets/Button",
	"umc/widgets/Uploader",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, tools, dialog, render, ConfirmDialog, StandbyMixin, Text, TextArea, Button, Uploader, _) {

	return declare('umc.modules.udm.LicenseImportDialog', [ConfirmDialog, StandbyMixin], {
		// summary:
		//		Class that provides the license import Dialog for UCS. It support importing a new license.

		closable: true,

		_widgets: null,

		title: _('Import of new UCS license'),

		postMixInProperties: function() {
			this.inherited(arguments);

			this.options = [{
				name: 'close',
				label: _('Close'),
				'default': true,
				callback: lang.hitch(this, function() {
					this.close();
				})
			}];

			this._widgets = render.widgets([{
				type : Text,
				name : 'titleImport',
				style : 'width: 100%',
				content : lang.replace('<h1>{title}</h1>', { title: _('Import new license') })
			}, {
				type: Text,
				name: 'message',
				content: _('New licenses that have been received after the activation of UCS or after a license purchase can be imported below. The license information can either be uploaded directly as file or it can be imported via copy and paste into the text field.') + '<br><br>'
			}, {
				type : TextArea,
				name : 'licenseText',
				label : _('License (as text)'),
				rows: 5,
				cols: 25
			}, {
				type : Uploader,
				name : 'licenseUpload',
				label : _('License (as file upload)'),
				command: 'udm/license/import',
				onUploaded: lang.hitch(this, function(result) {
					if (typeof result == "string") {
						// Apache gateway timeout error (?)
						return;
					}
					this._handleUploaded(result);
				})
			}, {
				type: Text,
				name: 'spacer',
				content: '&nbsp;&nbsp;'
			}]);

			var buttons = [{
				type : Button,
				name : 'btnLicenseText',
				label : _('Upload'),
				callback: lang.hitch(this, function() {
					var license = this._widgets.licenseText.get('value');
					this.standbyDuring(tools.umcpCommand('udm/license/import', { 'license': license }).then(
						lang.hitch(this, function(response) {
							this._handleUploaded(response.result[0]);
						})
					));
				})
			}];

			this.message = render.layout(['titleImport', 'message', 'licenseUpload', 'spacer', 'licenseText', 'btnLicenseText'], this._widgets, render.buttons(buttons));
		},

		_handleUploaded: function(result) {
			if (result.success) {
				dialog.alert(_('The license has been imported successfully'));
			} else {
				dialog.alert(_('The import of the license has failed: ') + result.message);
			}
		}
	});
});

