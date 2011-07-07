/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets._FormWidgetMixin", null, {
	required: false,

	//
	// methods/variables for validation
	//

	valid: null,

	isValid: function() {
		// use the property 'valid' in case it has been set
		// otherwise fall back to the default
		if (null !== this.valid) {
			return this.get('valid');
		}
		return this.inherited(arguments);
	},

	_setValidAttr: function(newVal) {
		this.valid = newVal;
		if (newVal || null === newVal) {
			this.set('state', '');
		}
		else {
			this.set('state', 'Error');
		}
	},

	setInvalid: function(message) {
		this.set('invalidMessage', message);
		this.set('valid', false);
	},

	setValid: function() {
		this.set('invalidMessage', '');
		this.set('valid', true);
	},

	resetValid: function() {
		// summary:
		//		Resets the default behaviour for validation.
		this.set('invalidMessage', '');
		this.set('valid', null);
	}
});

