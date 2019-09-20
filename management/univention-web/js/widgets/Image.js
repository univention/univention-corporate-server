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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dijit/layout/ContentPane",
	"umc/widgets/_FormWidgetMixin"
], function(declare, lang, ContentPane, _FormWidgetMixin) {
	return declare("umc.widgets.Image", [ ContentPane, _FormWidgetMixin ], {
		// the widget's class name as CSS class
		baseClass: 'umcImage',

		// imageType: String
		//		Image type: '*', 'jpeg', 'png', 'svg+xml'
		imageType: '*',

		// value: String
		//		base64 encoded string that contains image data.
		value: null,

		sizeClass: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			this.sizeClass = null;
		},

		// expects value to be base64 encoded image
		_getImageType: function() {
			// check the signature of the first bytes...
			// for jpeg it is (in hex): hex pattern: FF D8 FF
			if (this.value.indexOf('/9j/4') === 0) {
				return 'jpeg';
			}
			// the first 8 bytes (in hex) should be matched: 89 50 4E 47 0D 0A 1A 0A
			// note that base64 encodes 6 bits per character...
			if (this.value.indexOf('iVBORw0KGg') === 0) {
				return 'png';
			}
			if (this.value.indexOf('R0lGODdh') === 0 || this.value.indexOf('R0lGODlh') === 0) {
				return 'gif';
			}
			// check whether file starts with '<svg', '<SVG', '<xml', or '<XML'...
			// as simple check that should work for most cases
			if (this.value.indexOf('PHN2Z') === 0 || this.value.indexOf('PFNWR') === 0 || this.value.indexOf('PFhNT') || this.value.indexOf('PHhtb')) {
				return 'svg+xml';
			}
			return 'unknown';
		},

		_setValueAttr: function(newVal) {
			this._set('value', (typeof newVal == "string") ? newVal : "");
			this._updateContent();
		},

		_setImageTypeAttr: function(newVal) {
			this._set('imageType', newVal);
			this._updateContent();
		},

		_updateContent: function() {
			if (!this.value) {
				this.set('content', '');
			}
			else {
				var imageType = this.imageType;
				if (imageType == '*') {
					imageType = this._getImageType();
				}
				this.set('content', lang.replace('<img src="data:image/{imageType};base64,{value}"/>', {
					imageType: imageType,
					value: this.value
				}));
			}
		}
	});
});

