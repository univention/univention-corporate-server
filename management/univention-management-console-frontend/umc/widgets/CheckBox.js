/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.CheckBox");

dojo.require("dijit.form.CheckBox");
dojo.require("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets.CheckBox", [ dijit.form.CheckBox, umc.widgets._FormWidgetMixin ], {
	// by default, the checkbox is turned off
	value: 'false', 

	// the widget's class name as CSS class
	'class': 'umcCheckBox',

	_setValueAttr: function(newValue) {
		this.set('checked', newValue == '0' || newValue == 'false' || newValue == 'FALSE' || !newValue ? false : true);
	},

	_getValueAttr: function() {
		return this.get('checked');
	}
});



