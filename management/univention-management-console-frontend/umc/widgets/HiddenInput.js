/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.HiddenInput");

dojo.require("dijit.form.TextBox");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.tools");

dojo.declare("umc.widgets.HiddenInput", [ dijit.form.TextBox, umc.widgets._FormWidgetMixin ], {
	type: 'hidden'
});



