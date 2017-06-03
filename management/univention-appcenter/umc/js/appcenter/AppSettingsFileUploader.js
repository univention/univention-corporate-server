/*
 * Copyright 2017 Univention GmbH
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
/*global define */

define([
	"dojo/_base/declare",
	"dojox/html/entities",
	"umc/widgets/Uploader",
	"umc/widgets/Text",
	"umc/tools",
	"umc/i18n!"
], function(declare, entities, Uploader, Text, tools, _) {
	return declare("umc.modules.appcenter.AppSettingsFileUploader", Uploader, {
		showClearButton: false,
		size: 'Two',
		buttonLabel: _('Upload new file'),

		buildRendering: function() {
			this.inherited(arguments);

			this._content = new Text({
				content: ''
			});
			this.addChild(this._content, 0);
		},

		_getValueAttr: function() {
			return this._uploadedValue;
		},

		updateView: function(value) {
			if (value) {
				this._uploadedValue = atob(value);
				value = entities.encode(this._uploadedValue);
			} else {
				this._uploadedValue = null;
				value = '&nbsp;';
			}
			this._content.set('content', '<pre>' + value + '</pre>');
		}
	});
});


