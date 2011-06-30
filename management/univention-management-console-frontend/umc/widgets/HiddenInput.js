/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.HiddenInput");

dojo.require("dijit.form.TextBox");
dojo.require("umc.tools");

dojo.declare("umc.widgets.HiddenInput", dijit.form.TextBox, {
	type: 'hidden'
});



