/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.ComboBox");

dojo.require("dijit.form.FilteringSelect");
dojo.require("dojo.data.ItemFileWriteStore");
dojo.require("umc.widgets._SelectMixin");
dojo.require("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets.ComboBox", [ dijit.form.FilteringSelect, umc.widgets._SelectMixin, umc.widgets._FormWidgetMixin ], {
	// search for the substring when typing
	queryExpr: '*${0}*',

	// no auto completion, otherwise this gets weired in combination with the '*${0}*' search
	autoComplete: false,

	_setValueAttr: function(val) {
		//console.log('# ComboBox: ' + this.name + '.set("value", "' + val + '")');
		this.inherited(arguments);
	}
});




