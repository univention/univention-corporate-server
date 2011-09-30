/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.NumberSpinner");

dojo.require("dijit.form.NumberSpinner");
dojo.require("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets.NumberSpinner", [ dijit.form.NumberSpinner, umc.widgets._FormWidgetMixin ], {
	// the widget's class name as CSS class
	'class': 'umcNumberSpinner'
});



