/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.TextBox");

dojo.require("dijit.form.ValidationTextBox");
dojo.require("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets.TextBox", [ dijit.form.ValidationTextBox, umc.widgets._FormWidgetMixin ], {
	// the widget's class name as CSS class
	'class': 'umcTextBox'
});



