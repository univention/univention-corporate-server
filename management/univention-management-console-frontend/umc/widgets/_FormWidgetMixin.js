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

	_isValidSubset: function() {
		// use the property 'valid' in case it has been set
		// otherwise fall back to the default
		if (null !== this.valid) {
			return this.get('valid');
		}
		return this.inherited(arguments);
	},

	setValid: function(isValid, message) {
		if (null === isValid || undefined === isValid) {
			// reset error state and message
			this.set('valid', null);
			this.set('state', '');
			this.set('invalidMessage', '');
			this._maskValidSubsetError = false;
		}
		else if (isValid) {
			// force valid state
			this.set('valid', true);
			this.set('state', '');
			this.set('invalidMessage', '');
			this._maskValidSubsetError = true;
		}
		else {
			// force invalid state
			this.set('valid', false);
			this.set('state', 'Error');
			this.set('invalidMessage', message);
			this._maskValidSubsetError = false;
		}
	}
});

