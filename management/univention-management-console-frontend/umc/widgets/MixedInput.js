/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.MixedInput");

dojo.require("dijit.layout.ContentPane");
dojo.require("umc.tools");

dojo.declare("umc.widgets.MixedInput", dijit.layout.ContentPane, {

	// dynamicValues: String
	//		see description at `umc.widgets._SelectMixin`
	dynamicValues: null,

	// depends: String?|String[]?
	//		see description at `umc.widgets._SelectMixin`
	depends: null,

	// store the original properties as specified by the user
	_userProperties: null,

	// store the currently displayed widget
	_widget: null,

	'class': 'umcNoBorder',

	constructor: function(/*Object*/ props) {
		// store user defined properties
		this._userProperties = props;

		// only copy the properties that we need, the rest is for the actual form widget
		this.dynamicValues = props.dynamicValues;
		umc.tools.assert(this.dynamicValues && dojo.isString(this.dynamicValues), "For MixedInput, the property 'dynamicValues' needs to be specified.");
		this.depends = props.depends;
		umc.tools.assert(this.depends, "For MixedInput, the property 'depends' needs to be specified.");
	},

	_loadValues: function(/*Object?*/ _dependValues) {
		// we need to have dependValues defined
		console.log('# _loadValues: ' + dojo.toJson(_dependValues));
		if (!dojo.isObject(_dependValues)) {
			return;
		}

		// check whether all necessary values are specified
		var dependValues = {};
		console.log('# check values');
		var tmpDepends = dojo.isArray(this.depends) ? this.depends : [ this.depends ];
		for (var i = 0; i < tmpDepends.length; ++i) {
			if (_dependValues[tmpDepends[i]]) {
				dependValues[tmpDepends[i]] = _dependValues[tmpDepends[i]];
			}
			else {
				// necessary value not given, don't populate the store
				return;
			}
		}

		// get new values from the server and create a new form widget dynamically
		console.log('# umcp command');
		umc.tools.umcpCommand(this.dynamicValues, dependValues).then(dojo.hitch(this, function(data) {
			// guess the form widget type based on the result that we get
			//   array      -> ComboBox
			//   true/false -> CheckBox
			//   otherwise  -> TextBox
			var newWidgetClass = 'umc.widgets.TextBox';
			if (dojo.isArray(data.result)) {
				newWidgetClass = 'umc.widgets.ComboBox';
			}
			else if (true === data.result || false === data.result || 'true' == data.result || 'false' == data.result) {
				newWidgetClass = 'umc.widgets.CheckBox';
			}
			console.log('# newWidgetClass: ' + newWidgetClass);

			// destroy old widget in case the type has changed and create a new one
			if (this._widget && this._widget.declaredClass != newWidgetClass) {
				console.log('# destroying old widget');

				// destroy widget
				this._widget.destroyRecursive();
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
				this._widget = new WidgetClass(this._userProperties);
				this.set('content', this._widget);
			}

			if (this._widget._setDynamicValues) {
				// clear all values and set the dynamic values, they don't need to be reloaded
				this._widget._clearValues();
				this._widget._setDynamicValues(data.result);
			}
			this._widget.startup();
		}));
	}

});

