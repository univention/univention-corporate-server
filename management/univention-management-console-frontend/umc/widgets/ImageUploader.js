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

dojo.provide("umc.widgets.ImageUploader");

dojo.require("umc.widgets.Uploader");
dojo.require("umc.widgets.Image");
dojo.require("umc.tools");

dojo.declare("umc.widgets.ImageUploader", [ umc.widgets.Uploader ], {
	'class': 'umcImageUploader',

	i18nClass: 'umc.app',

	// imageType: String
	//		Image type: 'jpeg', 'png'
	imageType: 'jpeg',

	maxSize: 262400,

	_image: null,

	constructor: function() {
		this.buttonLabel = this._('Upload new image');
		this.clearButtonLabel = this._('Clear image data');
	},

	postMixInProperties: function() {
		this.inherited(arguments);

		this.sizeClass = null;
	},

	buildRendering: function() {
		this.inherited(arguments);

		// create an image widget
		this._image = new umc.widgets.Image({
			imageType: this.imageType
		});
		this.addChild(this._image, 0);
	},

	updateView: function(value, data) {
		this._image.set('value', value);
	}
});



