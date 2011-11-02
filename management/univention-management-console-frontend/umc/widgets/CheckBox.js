/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.CheckBox");

dojo.require("dijit.form.CheckBox");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.tools");

dojo.declare("umc.widgets.CheckBox", [ dijit.form.CheckBox, umc.widgets._FormWidgetMixin ], {
	// by default, the checkbox is turned off
	value: false,

	// the widget's class name as CSS class
	'class': 'umcCheckBox',

	// a checkbox is always true
	valid: true,

	// internal cache of the initial value
	_initialValue: null,

	postMixInProperties: function() {
		this._initialValue = this.value;
		this.inherited( arguments );
		this.sizeClass = null;
	},

	postCreate: function() {
		this.set('checked', umc.tools.isTrue(this._initialValue));
	},

	_setValueAttr: function(newValue) {
		this.set('checked', umc.tools.isTrue(newValue));
	},

	_getValueAttr: function() {
		return this.get('checked');
	}
});



