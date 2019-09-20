/*
 * Copyright 2013-2019 Univention GmbH
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
	"dojo/dom-class",
	"umc/tools",
	"umc/dialog",
	"umc/render",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Text",
	"umc/widgets/TextArea",
	"umc/widgets/Uploader",
	"umc/widgets/ProgressBar",
	"umc/widgets/Button",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, domClass, tools, dialog, render, ContainerWidget, ConfirmDialog, StandbyMixin, Text, TextArea, Uploader, ProgressBar, Button, _) {

	return declare('umc.modules.udm.LicenseImportDialog', [ConfirmDialog, StandbyMixin], {
		// summary:
		//		Class that provides the license import Dialog for UCS. It support importing a new license.

		// umcPopup for content styling; umcConfirmDialog for max-width
		'class': 'umcPopup umcConfirmDialog umcUdmLicenseImportDialog',

		closable: true,
		options: [],

		_widgets: null,

		_progressBar: null,

		title: _('UCS license import'),

		postMixInProperties: function() {
			this.inherited(arguments);

			// create a progress bar widget
			this._progressBar = new ProgressBar({});
			this.own(this._progressBar);

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
				content: '<p>' + _('New license keys can be imported here. You receive these keys after the activation of UCS or after a license purchase. The key can either be uploaded directly as file or it can be imported via copy and paste into the text field.') + '</p>'
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
			}, {
				type: Button,
				name : 'btnLicenseText',
				label : _('Import from text field'),
				callback: lang.hitch(this, function() {
					var license = this._widgets.licenseText.get('value');
					if (!lang.trim(license)) {
						dialog.alert(_('The text field is empty. Please copy all lines of the license file into the text field and retry to import the data.'));
						return;
					}
					this._progressBar.setInfo(_('Importing license data...'), null, Infinity);
					this.standbyDuring(tools.umcpCommand('udm/license/import', { 'license': license }).then(
						lang.hitch(this, function(response) {
							return this._handleUploaded(response.result[0]);
						})
					), this._progressBar);
				})
			}]);

			this.options = [{
				'default': true,
				name: 'close',
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
				'btnLicenseText'
			], this._widgets);
			domClass.add(content.domNode, 'col-xxs-12 col-xs-8');
			domClass.add(this._widgets.btnLicenseText.$refLabel$.domNode, 'umcUploader');
			this.message.addChild(content);
		},

		_handleUploaded: function(result) {
			if (result.success) {
				this._progressBar.setInfo(_('Updating session data...'), null, Infinity);
				return tools.renewSession().then(lang.hitch(this, function() {
					this.hide();
					dialog.alert(_('The license has been imported successfully.'));
				}));

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

