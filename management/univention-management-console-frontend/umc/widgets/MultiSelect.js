/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.MultiSelect");

dojo.require("dojox.form.CheckedMultiSelect");
dojo.require("dojo.data.ItemFileWriteStore");
dojo.require("umc.widgets._SelectMixin");
dojo.require("umc.tools");

dojo.declare("umc.widgets.MultiSelect", [ dojox.form.CheckedMultiSelect, umc.widgets._SelectMixin ], {
	multiple: true,
	size: 5,

	constructor: function(props) {
		dojo.mixin(this, props);

		// _SelectMixin method
		this._setupStore();
	},

	postMixInProperties: function() {
		this.inherited(arguments);

		// _SelectMixin method
		this._saveInitialValue();
	},

	startup: function() {
		this.inherited(arguments);

		// _SelectMixin method
		this._loadValues();
	},

	_setValueAttr: function(/*String|Array*/ values) {
		// convenience method to handle string list or array
		umc.tools.assert(dojo.isString(values) || dojo.isArray(values),
				'The value type for MultiSelect needs to be a comma separated list of strings or an array.');

		// in case we have a string, assume it is a comma separated list of values
		// and transform it into an array
		if (dojo.isString(values)) {
			values = values.split(',');
		}

		// call parents method
		this.inherited('_setValueAttr', [values]);
	}
});


