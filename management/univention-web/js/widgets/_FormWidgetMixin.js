/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,console */

define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dojox/html/entities"
], function(declare, domClass, entities) {
	return declare("umc.widgets._FormWidgetMixin", null, {
		// by default, set required to 'false'
		required: false,

		sizeClass: 'One',

		visible: true,

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
			domClass.add( this.domNode, 'umcFormWidget' );
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
			// fallback to inherited method:
			// not all of our widgets (or the dijit base classes)
			//   define "isValid", in this case return true
			// see Bug#30965
			var superIsValid = this.getInherited(arguments);
			if (superIsValid !== undefined) {
				return superIsValid.apply(this, arguments);
			} else {
				// was not defined
				return true;
			}
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
				this.set('invalidMessage', entities.encode(message));
				this._maskValidSubsetError = false;
			}
			return true;
		},

		validate: function() {
			var val = this.inherited(arguments);
			if (val === undefined) {
				return this.isValid();
			}
			return val;
		},

		focus: function() {
			this.inherited(arguments);
		},

		focusInvalid: function() {
			if ('validate' in this && typeof this.validate === 'function') {
				this._hasBeenBlurred = true;
				this.validate();
			}
			this.focus();
		},

		show: function() {
			this.set( 'visible', true );
		},

		hide: function() {
			this.set( 'visible', false );
		},

		_setVisibleAttr: function(newVal) {
			this._set('visible', newVal);
			domClass.toggle(this.domNode, 'dijitDisplayNone', !newVal);
		}
	});
});
