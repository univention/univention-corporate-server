/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Button");

dojo.require("dijit.form.Button");

dojo.declare("umc.widgets.Button", dijit.form.Button, {
	// defaultButton: Boolean
	//		If set to 'true', button will be rendered as default, i.e., submit button.
	defaultButton: false,

	// callback: Function
	//		Convenience property for onClick callback handler.
	callback: null,

	// the widget's class name as CSS class
	'class': 'umcButton',

	type: 'button',

	constructor: function(props) {
		dojo.mixin(this, props);
		if (this.defaultButton) {
			this['class'] = 'umcSubmitButton';
		}
	},

	postCreate: function() {
		this.inherited(arguments);

		if (dojo.isFunction(this.callback)) {
			this.connect(this, 'onClick', 'callback');
		}
	}
});



