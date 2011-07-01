/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.PasswordBox");

dojo.require("dijit.form.ValidationTextBox");
dojo.require("umc.tools");

dojo.declare("umc.widgets.PasswordBox", dijit.form.ValidationTextBox, {
	type: 'password'
});



