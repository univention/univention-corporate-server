/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.DateBox");

dojo.require("dijit.form.DateTextBox");
dojo.require("dojox.string.sprintf");
dojo.require("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets.DateBox", [ dijit.form.DateTextBox, umc.widgets._FormWidgetMixin ], {
	// return ISO8601/RFC3339 format (yyyy-MM-dd) as string
	_getValueAttr: function() {
		var date = this.inherited(arguments);
		if (date && date instanceof Date) {
			return dojox.string.sprintf('%04d-%02d-%02d', date.getFullYear(), date.getMonth(), date.getDate());
		}
		return date;
	}
});



