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



