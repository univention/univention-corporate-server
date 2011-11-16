/*
 * Copyright 2011 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
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
		dojo.addClass( this.domNode, 'umcFormWidget' );
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

