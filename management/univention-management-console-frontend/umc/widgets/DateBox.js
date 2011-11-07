/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.DateBox");

dojo.require("dijit.form.DateTextBox");
dojo.require("dojox.string.sprintf");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");
dojo.require("umc.tools");

dojo.declare("umc.widgets.DateBox", [ 
	umc.widgets.ContainerWidget, 
	umc.widgets._FormWidgetMixin,
	umc.widgets._WidgetsInWidgetsMixin
], {
	// the widget's class name as CSS class
	'class': 'umcDateBox',

	_dateBox: null,

	sizeClass: null,

	disabled: false,

	postMixInProperties: function() {
		this.inherited(arguments);

		this.sizeClass = null;
	},

	buildRendering: function() {
		this.inherited(arguments);

		this._dateBox = this.adopt(dijit.form.DateTextBox, {
			name: this.name,
			disabled: this.disabled
		});
		this.addChild(this._dateBox);

		// hook to the onChange event
		this.connect(this._dateBox, 'onChange', 'onChange');
	},

	// return ISO8601/RFC3339 format (yyyy-MM-dd) as string
	_getValueAttr: function() {
		var date = this._dateBox.get('value');
		if (date && date instanceof Date) {
			return dojox.string.sprintf('%04d-%02d-%02d', date.getFullYear(), date.getMonth() + 1, date.getDate());
		}
		return date;
	},

	_setValueAttr: function(newVal) {
		this._dateBox.set('value', newVal);
	},

	isValid: function() {
		// use the property 'valid' in case it has been set
		// otherwise fall back to the default
		if (null !== this.valid) {
			return this.get('valid');
		}
		return this._dateBox.isValid();
	},

	_setBlockOnChangeAttr: function(/*Boolean*/ value) {
		// execute the inherited functionality in the widget's scope
		umc.tools.delegateCall(this, arguments, this._dateBox);
	},

	_getBlockOnChangeAttr: function(/*Boolean*/ value) {
		// execute the inherited functionality in the widget's scope
		umc.tools.delegateCall(this, arguments, this._dateBox);
	}
});



