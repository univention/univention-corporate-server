/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.TextBox");

dojo.require("dijit.form.ValidationTextBox");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.tools");

dojo.declare("umc.widgets.TextBox", [ dijit.form.ValidationTextBox, umc.widgets._FormWidgetMixin ], {
	// the widget's class name as CSS class
	'class': 'umcTextBox',

	// dynamicValue: String|Function
	//		Either an UMCP command to query a value from or a javascript function.
	//		The javascript function may return a String or a dojo.Deferred object.
	dynamicValue: null,

	// depends: String?|String[]?
	//		Specifies that values need to be loaded dynamically depending on
	//		other form fields.
	depends: null,

	// umcpCommand:
	//		Reference to the umcpCommand the widget should use.
	//		In order to make the widget send information such as module flavor
	//		etc., it can be necessary to specify a module specific umcpCommand
	//		method.
	umcpCommand: umc.tools.umcpCommand,

	//FIXME: the name should be different from _loadValues, e.g., _dependencyUpdate,
	//       and the check for all met dependencies should be done in the Form
	_loadValues: function(/*Object?*/ params) {
		// mixin additional options for the UMCP command
		if (this.dynamicOptions && dojo.isObject(this.dynamicOptions)) {
			dojo.mixin(params, this.dynamicOptions);
		}

		// get the dynamic values, block concurrent events for value loading
		var func = umc.tools.stringOrFunction(this.dynamicValue, this.umcpCommand);
		var deferredOrValues = func(params);

		// make sure we have an array or a dojo.Deferred object
		if (deferredOrValues) {
			dojo.when(deferredOrValues, dojo.hitch(this, function(res) {
				this.set('value', res);
			}));
		}
	}
});



