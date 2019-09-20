/*
 * Copyright 2017-2019 Univention GmbH
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
/*global define */

define([
	"dojo/_base/declare",
	"dojox/html/entities",
	"umc/widgets/Uploader",
	"umc/widgets/Text",
	"umc/tools",
	"umc/i18n!umc/modules/appcenter"
], function(declare, entities, Uploader, Text, tools, _) {
	return declare("umc.modules.appcenter.AppSettingsFileUploader", Uploader, {
		size: 'Two',
		buttonLabel: _('Upload file'),
		clearButtonLabel: _('Delete file'),
		fileName: null,

		buildRendering: function() {
			this.inherited(arguments);

			this._content = new Text({
				content: ''
			});
			this.addChild(this._content, 0);
			this._originalValue = null;
			if (this.data && this.data.content) {
				this._originalValue = this.data.content;
			}
		},

		_getValueAttr: function() {
			return this._uploadedValue;
		},

		validate: function() {
			if (this.required && !this._uploadedValue) {
				return false;
			}
			return true;
		},

		updateView: function(value) {
			var lengthContent = '';
			if (this._originalValue) {
				lengthContent += _('A file is present.') + ' ';
			} else {
				lengthContent += _('No file was uploaded yet.') + ' ';
			}
			if (value) {
				this._uploadedValue = value;
				lengthContent += _('After saving, the new file will be uploaded.');
			} else {
				this._uploadedValue = null;
				if (this._originalValue) {
					lengthContent += _('After saving, the file will be deleted.');
				}
			}
			this._content.set('content', _('File will be uploaded to %s.', '<em>' + this.fileName + '</em>') + ' ' + lengthContent);
		}
	});
});


