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


