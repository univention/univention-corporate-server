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
	"dijit/Dialog",
	"umc/tools",
	"umc/dialog",
	"umc/render",
	"umc/widgets/ContainerWidget",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Text",
	"umc/widgets/TextArea",
	"umc/widgets/Button",
	"umc/widgets/Uploader",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, Dialog, tools, dialog, render, ContainerWidget, StandbyMixin, Text, TextArea, Button, Uploader, _) {

	return declare('umc.modules.udm.LicenseImportDialog', [Dialog, StandbyMixin], {
		// summary:
		//		Class that provides the license import Dialog for UCS. It support importing a new license.

		// the widget's class name as CSS class
		'class': 'umcPopup',

		_widgets: null,

		_container: null,

		title: _('Import of new UCS license'),

		buildRendering: function() {
			this.inherited(arguments);

			// put buttons into separate container
			var _buttonContainer = new ContainerWidget({
				style: 'text-align: center;',
				'class': 'umcButtonRow'
			});
			_buttonContainer.addChild(new Button({
				label: _('Close'),
				defaultButton: true,
				onClick: lang.hitch(this, function() {
					this.hide();
				})
			}));

			var widgets = [{
				type : TextArea,
				name : 'licenseText',
				label : _('License (as text)')
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
					this.handleUploaded(result);
				})
			}, {
				type : Text,
				name : 'titleImport',
				style : 'width: 100%',
				content : lang.replace('<h1>{title}</h1>', { title: _('Import new license') })
			}, {
				type: Text,
				name: 'spacer',
				content: '&nbsp;&nbsp;'
			}];

			var buttons = [{
				type : Button,
				name : 'btnLicenseText',
				label : _('Upload'),
				callback: lang.hitch(this, function() {
					var license = this._widgets.licenseText.get('value');
					this.standbyDuring(tools.umcpCommand('udm/license/import', { 'license': license }).then(
						lang.hitch(this, function(response) {
							this.handleUploaded(response.result[0]);
						})
					));
				})
			}];

			this._widgets = render.widgets(widgets);
			var _buttons = render.buttons(buttons);
			var _container = render.layout(['titleImport', 'licenseUpload', 'spacer', 'licenseText', 'btnLicenseText'], this._widgets, _buttons);

			var _content = new ContainerWidget({});
			_content.addChild(_container);

			// put the layout together
			this._container = new ContainerWidget({
				style: 'width: 600px'
			});
			this._container.addChild(_content);
			this._container.addChild(_buttonContainer);
			this.addChild(this._container);
			this.on('hide', lang.hitch(this, function() {
				this.destroyRecursive();
			}));
		},

		handleUploaded: function(result) {
			if (result.success) {
				dialog.alert(_('The license has been imported successfully'));
			} else {
				dialog.alert(_('The import of the license has failed: ') + result.message);
			}
		}
	});
});

