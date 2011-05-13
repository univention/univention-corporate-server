/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.ComboBox");

dojo.require("dijit.form.FilteringSelect");
dojo.require("dojo.data.ItemFileWriteStore");
dojo.require("umc.widgets._SelectMixin");
dojo.require("umc.tools");

dojo.declare("umc.widgets.ComboBox", [ dijit.form.FilteringSelect, umc.widgets._SelectMixin ], {
	constructor: function() {
		// _SelectMixin method
		this._setupStore();
	},

	postMixInProperties: function() {
		this.inherited(arguments);

		// _SelectMixin method
		this._saveInitialValue();
	},

	postCreate: function() {
		this.inherited(arguments);

		// _SelectMixin method
		this._populateStore();
	}
});


