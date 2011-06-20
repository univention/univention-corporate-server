/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.CheckBox");

dojo.require("dijit.form.CheckBox");

dojo.declare("umc.widgets.CheckBox", dijit.form.CheckBox, {
	_getValueAttr: function() {
		return this.inherited(arguments) ? true : false;
	}
});



