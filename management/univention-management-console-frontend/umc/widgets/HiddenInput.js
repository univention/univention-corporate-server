/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.HiddenInput");

dojo.require("dijit.form.TextBox");
dojo.require("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets.HiddenInput", [ dijit.form.TextBox, umc.widgets._FormWidgetMixin ], {
	type: 'hidden',

	// the widget's class name as CSS class
	'class': 'umcHiddenInput'
});



