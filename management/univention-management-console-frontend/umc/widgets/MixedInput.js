/*
 * Copyright 2011-2012 Univention GmbH
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

dojo.provide("umc.widgets.MixedInput");

dojo.require("dijit.layout.ContentPane");
dojo.require("umc.tools");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.widgets.MixedInput", [
	dijit.layout.ContentPane,
	umc.widgets._FormWidgetMixin,
	umc.widgets._WidgetsInWidgetsMixin
], {
	// umcpCommand:
	//		Reference to the umcpCommand the widget should use.
	//		In order to make the widget send information such as module flavor
	//		etc., it can be necessary to specify a module specific umcpCommand
	//		method.
	umcpCommand: umc.tools.umcpCommand,

	// dynamicValues: String|Function
	//		see description at `umc.widgets._SelectMixin`
	dynamicValues: null,

	// dynamicOptions: Object?
	//		see description at `umc.widgets._SelectMixin`
	dynamicOptions: null,

	// depends: String?|String[]?
	//		see description at `umc.widgets._SelectMixin`
	depends: null,

	// disabled: Boolean?
	//		Disables the widget for user input.
	disabled: false,

	// the widget's class name as CSS class
	'class': 'umcMixedInput',

	// store the original properties as specified by the user
	_userProperties: null,

	// store the currently displayed widget
	_widget: null,

	style: 'padding: 0',

	constructor: function(/*Object*/ props) {
		// mixin in the 'disabled' property
		props.disabled = this.disabled;

		// store user defined properties
		this._userProperties = dojo.clone(props);

		// only copy the properties that we need, the rest is for the actual form widget
		this.dynamicValues = props.dynamicValues;
		umc.tools.assert(this.dynamicValues && (dojo.isString(this.dynamicValues) || dojo.isFunction(this.dynamicValues)), "For MixedInput, the property 'dynamicValues' needs to be specified.");
		this.depends = props.depends;
		//umc.tools.assert(this.depends, "For MixedInput, the property 'depends' needs to be specified.");
		this.umcpCommand = props.umcpCommand || umc.tools.umcpCommand;
	},

	postMixInProperties: function() {
		this.inherited(arguments);

		this._userProperties.sizeClass = this.sizeClass;
		this.sizeClass = null;
	},

	buildRendering: function() {
		this.inherited(arguments);

		// initial widget is a TextBox
		this._setValues('');
	},

	postCreate: function() {
		this.inherited(arguments);

		// invoke the loading of dynamic values in case we do not have any dependencies
		if (!this.depends || !this.depends.length) {
			this._loadValues();
		}
	},

	_loadValues: function(/*Object?*/ _dependValues) {
		// unify `depends` property to be an array
		var dependList = dojo.isArray(this.depends) ? this.depends :
			(this.depends && dojo.isString(this.depends)) ? [ this.depends ] : [];

		// check whether all necessary values are specified
		var params = {};
		var nDepValues = 0;
		if (dependList.length && dojo.isObject(_dependValues)) {
			// check whether all necessary values are specified
			for (var i = 0; i < dependList.length; ++i) {
				if (_dependValues[dependList[i]]) {
					params[dependList[i]] = _dependValues[dependList[i]];
					++nDepValues;
				}
			}
		}

		// only load dynamic values in case all dependencies are fullfilled
		if (dependList.length != nDepValues) {
			return;
		}

		// mixin additional options for the UMCP command
		if (this.dynamicOptions && dojo.isObject(this.dynamicOptions)) {
			dojo.mixin(params, this.dynamicOptions);
		}
		else if (this.dynamicOptions && dojo.isFunction(this.dynamicOptions)) {
			var res = this.dynamicOptions();
			umc.tools.assert(res && dojo.isObject(res), 'The return type of a function specified by umc.widgets.MixedInput.dynamicOptions() needs to return a dictionary: ' + dojo.toJson(res));
			dojo.mixin(params, res);
		}

		// get new values from the server and create a new form widget dynamically
		this.umcpCommand(this.dynamicValues, params).then(dojo.hitch(this, function(data) {
			this._setValues(data.result);
		}));
	},

	_setValues: function(values) {
		// guess the form widget type based on the result that we get
		//   array      -> ComboBox
		//   true/false -> CheckBox
		//   otherwise  -> TextBox
		var newWidgetClass = 'umc.widgets.TextBox';
		if (dojo.isArray(values)) {
			newWidgetClass = 'umc.widgets.ComboBox';
		}
		else if (true === values || false === values || 'true' == values || 'false' == values) {
			newWidgetClass = 'umc.widgets.CheckBox';
		}

		// destroy old widget in case the type has changed and create a new one
		if (this._widget && this._widget.declaredClass != newWidgetClass) {
			// destroy widget
			this.orphan(this._widget, true);
			this._widget = null;
		}

		// check whether we need to create a new widget
		if (!this._widget) {
			// create the new widget according to its type
			dojo['require'](newWidgetClass);
			var WidgetClass = dojo.getObject(newWidgetClass);
			if (!WidgetClass) {
				throw new Error('MixedInput: Could not instantiate the class ' + newWidgetClass);
			}
			this._widget = this.adopt(WidgetClass, this._userProperties);
			this.set('content', this._widget);

			// hook to the onChange event
			this.connect(this._widget, 'onChange', 'onChange');
		}

		// set the indicated values
		if (this._widget._setDynamicValues) {
			// clear all values and set the dynamic values, they don't need to be reloaded
			this._widget._clearValues();
			this._widget._setDynamicValues(values);
		}
		else if (!dojo.isArray(values)) {
			this._widget.set('value', values);
		}
		this._widget.startup();

		this.onValuesLoaded();
	},

	_setValueAttr: function(newVal) {
		if (this._widget) {
			this._widget.set('value', newVal);
		}
	},

	_getValueAttr: function() {
		if (this._widget) {
			return this._widget.get('value');
		}
		return undefined;
	},

	isValid: function() {
		if (this._widget) {
			return this._widget.isValid.apply(this._widget, arguments);
		}
		return true;
	},

	setValid: function() {
		if (this._widget) {
			this._widget.setValid.apply(this._widget, arguments);
		}
	},

	_setBlockOnChangeAttr: function(/*Boolean*/ value) {
		// execute the inherited functionality in the widget's scope
		if (this._widget) {
			umc.tools.delegateCall(this, arguments, this._widget);
		}
	},

	_getBlockOnChangeAttr: function(/*Boolean*/ value) {
		// execute the inherited functionality in the widget's scope
		if (this._widget) {
			umc.tools.delegateCall(this, arguments, this._widget);
		}
	},

	onValuesLoaded: function() {
		// event stub
	},

	focus: function() {
		if (dojo.getObject('_widget.focus', false, this)) {
			this._widget.focus();
		}
	}
});

