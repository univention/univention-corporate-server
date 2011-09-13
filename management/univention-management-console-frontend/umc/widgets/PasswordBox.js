/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.PasswordBox");

dojo.require("umc.widgets.TextBox");
dojo.require("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets.PasswordBox", [ umc.widgets.TextBox, umc.widgets._FormWidgetMixin ], {
	type: 'password',

	// the widget's class name as CSS class
	'class': 'umcPasswordBox'
});



