/*
 * Copyright 2011-2012 Univention GmbH
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
/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Image");

dojo.require("umc.tools");
dojo.require("dijit.layout.ContentPane");
dojo.require("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets.Image", [ dijit.layout.ContentPane, umc.widgets._FormWidgetMixin ], {
	// the widget's class name as CSS class
	'class': 'umcImage',

	// imageType: String
	//		Image type: 'jpeg', 'png'
	imageType: 'jpeg',

	// value: String
	//		base64 encoded string that contains image data.
	value: null,

	sizeClass: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		this.sizeClass = null;
	},

	_setValueAttr: function(newVal) {
		this.value = dojo.isString(newVal) ? newVal : "";
		this._updateContent();
	},

	_setImageTypeAttr: function(newVal) {
		this.imageType = newVal;
		this._updateContent();
	},

	_updateContent: function() {
		if (!this.value) {
			this.set('content', '');
		}
		else {
			this.set('content', dojo.replace('<img src="data:image/{imageType};base64,{value}"/>', this));
		}
	}
});


