/*
 * Copyright 2011-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define,require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/Deferred",
	"dojo/when",
	"dojo/json",
	"dijit/layout/ContentPane",
	"umc/tools",
	"umc/widgets/_FormWidgetMixin",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/widgets/CheckBox"
], function(declare, lang, Deferred, when, json, ContentPane, tools, _FormWidgetMixin) {
	return declare("umc.widgets.MixedInput", [ ContentPane, _FormWidgetMixin ], {
		// umcpCommand:
		//		Reference to the umcpCommand the widget should use.
		//		In order to make the widget send information such as module flavor
		//		etc., it can be necessary to specify a module specific umcpCommand
		//		method.
		umcpCommand: lang.hitch(tools, 'umcpCommand'),

		// dynamicValues: String|Function
		//		see description at `umc/widgets/_SelectMixin`
		dynamicValues: null,

		// dynamicOptions: Object?
		//		see description at `umc/widgets/_SelectMixin`
		dynamicOptions: null,

		// depends: String?|String[]?
		//		see description at `umc/widgets/_SelectMixin`
		depends: null,

		// disabled: Boolean?
		//		Disables the widget for user input.
		disabled: false,

		// the widget's class name as CSS class
		baseClass: 'umcMixedInput',

		// store the original properties as specified by the user
		_userProperties: null,

		// store the currently displayed widget
		_widget: null,

		_readyDeferred: null,

		constructor: function(/*Object*/ props) {
			// mixin in the 'disabled' property
			props.disabled = this.disabled;

			// store user defined properties
			this._userProperties = lang.clone(props);

			// only copy the properties that we need, the rest is for the actual form widget
			this.dynamicValues = props.dynamicValues;
			tools.assert(this.dynamicValues && (typeof this.dynamicValues == "string" || typeof this.dynamicValues == "function"), "For MixedInput, the property 'dynamicValues' needs to be specified.");
			this.depends = props.depends;
			//tools.assert(this.depends, "For MixedInput, the property 'depends' needs to be specified.");
			this.umcpCommand = props.umcpCommand || lang.hitch(tools, 'umcpCommand');
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this._readyDeferred = new Deferred();
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
			var dependList = this.depends instanceof Array ? this.depends :
				(this.depends && typeof this.depends == "string") ? [ this.depends ] : [];

			// check whether all necessary values are specified
			var params = {};
			var nDepValues = 0;
			if (dependList.length && typeof _dependValues == "object") {
				// check whether all necessary values are specified
				for (var i = 0; i < dependList.length; ++i) {
					if (_dependValues[dependList[i]]) {
						params[dependList[i]] = _dependValues[dependList[i]];
						++nDepValues;
					}
				}
			}

			// only load dynamic values in case all dependencies are fulfilled
			if (dependList.length != nDepValues) {
				return;
			}

			// initiate a new Deferred object in case there is none already pending
			if (this._readyDeferred.isFulfilled()) {
				this._readyDeferred = new Deferred();
			}

			// mixin additional options for the UMCP command
			if (this.dynamicOptions && typeof this.dynamicOptions == "object") {
				lang.mixin(params, this.dynamicOptions);
			}
			else if (this.dynamicOptions && typeof this.dynamicOptions == "function") {
				var res = this.dynamicOptions();
				tools.assert(res && typeof res == "object", 'The return type of a function specified by umc/widgets/MixedInput::dynamicOptions() needs to return a dictionary: ' + json.stringify(res));
				lang.mixin(params, res);
			}

			// get new values from the server and create a new form widget dynamically
			var func = tools.stringOrFunction(this.dynamicValues, this.umcpCommand);
			var deferredOrValues = func(params);
			when(deferredOrValues, lang.hitch(this, '_setValues'));
		},

		_setValues: function(values) {
			// guess the form widget type based on the result that we get
			//   array      -> ComboBox
			//   true/false -> CheckBox
			//   otherwise  -> TextBox
			var newWidgetClass = 'umc/widgets/TextBox';
			if (values instanceof Array) {
				newWidgetClass = 'umc/widgets/ComboBox';
			}
			else if (true === values || false === values || 'true' == values || 'false' == values) {
				newWidgetClass = 'umc/widgets/CheckBox';
			}

			// destroy old widget in case the type has changed and create a new one
			if (this._widget && this._widget.declaredClass != newWidgetClass.replace(/\//g, '.')) {
				// destroy widget
				this._widget.destroy();
				this._widget = null;
			}

			// check whether we need to create a new widget
			if (!this._widget) {
				// create the new widget according to its type
				var WidgetClass = require(newWidgetClass);
				if (!WidgetClass) {
					throw new Error('MixedInput: Could not instantiate the class ' + newWidgetClass);
				}
				this._widget = this.own(new WidgetClass(this._userProperties))[0];
				this.set('content', this._widget);

				// propagate value changes
				this._widget.own(this._widget.watch('value', lang.hitch(this, function(name, oldVal, newVal) {
					this._set(name, newVal);
				})));
			}

			// set the indicated values
			if (this._widget._setDynamicValues) {
				// clear all values and set the dynamic values, they don't need to be reloaded
				this._widget._clearValues();
				this.set('value', this._initialValue);
				this._widget._setDynamicValues(values);
			}
			else if (!(values instanceof Array)) {
				this._widget.set('value', values);
			}
			this._widget.startup();

			this.onValuesLoaded();
			this._readyDeferred.resolve();
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
				tools.delegateCall(this, arguments, this._widget);
			}
		},

		_getBlockOnChangeAttr: function(/*Boolean*/ value) {
			// execute the inherited functionality in the widget's scope
			if (this._widget) {
				tools.delegateCall(this, arguments, this._widget);
			}
		},

		onValuesLoaded: function() {
			// event stub
		},

		focus: function() {
			if (lang.getObject('_widget.focus', false, this)) {
				this._widget.focus();
			}
		},

		// ready:
		//		Returns null or a Deferred which resolves as soon as any
		//		loading activity of the widget is finished.
		ready: function() {
			return this._readyDeferred;
		}
	});
});
