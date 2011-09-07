/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.SubmitButton");

dojo.require("umc.widgets.Button");

dojo.declare("umc.widgets.SubmitButton", umc.widgets.Button, {
	type: 'submit',

	// the widget's class name as CSS class
	'class': 'umcSubmitButton'
});

