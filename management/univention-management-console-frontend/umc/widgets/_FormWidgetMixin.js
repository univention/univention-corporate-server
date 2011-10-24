/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets._FormWidgetMixin");

dojo.declare("umc.widgets._FormWidgetMixin", null, {
	// by default, set required to 'false'
	required: false,

	sizeClass: 'One',

	//
	// event handling
	//

	// blockOnChange:
	//		Set this variable to true in order to avoid notifications of onChange
	//		events. Use set()/get() methods to access this property.
	blockOnChange: undefined,

	_setBlockOnChangeAttr: function(/*Boolean*/ value) {
		this._onChangeActive = !value;
	},

	_getBlockOnChangeAttr: function(/*Boolean*/ value) {
		return this._onChangeActive;
	},

	postCreate: function() {
		this.inherited( arguments );

		if ( this.sizeClass ) {
			dojo.addClass( this.domNode, 'umcSize-' + this.sizeClass );
		}
	},

	// provide 'onChange' method stub in case it does not exist yet
	onChange: function(newValue) {
		// event stub
	},

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

