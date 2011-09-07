/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.PasswordBox");

dojo.require("dijit.form.ValidationTextBox");
dojo.require("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets.PasswordBox", [ dijit.form.ValidationTextBox, umc.widgets._FormWidgetMixin ], {
	type: 'password',

	// the widget's class name as CSS class
	'class': 'umcPasswordBox'
});



