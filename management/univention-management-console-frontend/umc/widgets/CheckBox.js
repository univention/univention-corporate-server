/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.CheckBox");

dojo.require("dijit.form.CheckBox");
dojo.require("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets.CheckBox", [ dijit.form.CheckBox, umc.widgets._FormWidgetMixin ], {
	// by default, the checkbox is turned off
	value: 'false', 

	_setValueAttr: function(newValue) {
		this.set('checked', newValue == '0' || newValue == 'false' || newValue == 'FALSE' || !newValue ? false : true);
	},

	_getValueAttr: function() {
		value = this.get('checked');

		if ( this.syntax == undefined ) {
			return value;
		}

		// try to map boolean value to UDM compatible string
		switch ( this.syntax ) {
			case "AllowDeny":
				return value ? "allow" : "deny";
			case "TrueFalseUp":
				return value ? "TRUE" : "FALSE";
			case "OkOrNot":
				return value ? "OK" : "Not";
			case "boolean":
				return value ? "1" : "0";
		}

		return value;
	}
});



