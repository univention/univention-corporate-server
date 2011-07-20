/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.DateBox");

dojo.require("dijit.form.DateTextBox");
dojo.require("dojox.string.sprintf");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets.DateBox", [ umc.widgets.ContainerWidget, umc.widgets._FormWidgetMixin ], {
	_dateBox: null,

	buildRendering: function() {
		this.inherited(arguments);

		this._dateBox = new dijit.form.DateTextBox({
			name: this.name
		});
		this.addChild(this._dateBox);
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
	}
});



