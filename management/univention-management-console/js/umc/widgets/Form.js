/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Form");

dojo.require("dijit.form.Form");

dojo.require("dojox.form.manager._Mixin");
dojo.require("dojox.form.manager._FormMixin");
dojo.require("dojox.form.manager._ValueMixin");
dojo.require("dojox.form.manager._EnableMixin");
dojo.require("dojox.form.manager._DisplayMixin");
dojo.require("dojox.form.manager._ClassMixin");
dojo.require("dojox.layout.TableContainer");

dojo.require("dojo.data.ItemFileWriteStore");
dojo.require("umc.widgets.ContainerForm");
dojo.require("umc.tools");

dojo.declare("umc.widgets.Form", [
		dijit.form.Form,
		dojox.form.manager._Mixin,
		dojox.form.manager._FormMixin,
		dojox.form.manager._ValueMixin,
		dojox.form.manager._EnableMixin,
		dojox.form.manager._DisplayMixin,
		dojox.form.manager._ClassMixin
], {
	// summary:
	//		Encapsulates a complete form, offers unified access to elements as
	//		well as some convenience methods.

	// widgets: Object[]
	//		Array of config objects that specify the widgets that are going to 
	//		be used in the form.
	widgets: null,

	// buttons: Object[]
	//		Array of config objects that specify the buttons that are going to 
	//		be used in the form. Buttons with the name 'submit' and 'reset' have
	//		standard handlers unless 
	buttons: null,

	// layout: String[][]
	//		Array of strings that specifies the position of each element in the
	//		layout.
	layout: null,

	// cols: Integer
	//		Number of columns (default is 2).
	cols: 2,

	_widgets: null,

	_buttons: null,

	_layoutContainer: null,

	buildRendering: function() {
		this.inherited(arguments);

		// render the widgets and the layout
		this._widgets = umc.tools.renderWidgets(this.widgets);
		this._buttons = umc.tools.renderButtons(this.buttons);
		this._layoutContainer = umc.tools.renderLayout(this.layout, this._widgets, this._buttons, this.cols);

		// start processing the layout information
		this._layoutContainer.placeAt(this.containerNode);
		this._layoutContainer.startup();
	},

	postCreate: function() {
		this.inherited(arguments);

		// register callbacks for onSubmit and onReset events
		dojo.connect(this, 'onSubmit', dojo.hitch(this, function(e) {
			// prevent standard form submission
			e.preventDefault();

			// if there is a custom callback, call it with all form values
			var customCallback = dojo.getObject('submit.callback', false, this._buttons) || function() { };
			customCallback(this.gatherFormValues());
		}));
		dojo.connect(this, 'onReset', dojo.hitch(this, function(e) {
			// if there is a custom callback, call it with all form values
			var customCallback = dojo.getObject('reset.callback', false, this._buttons) || function() { };
			customCallback(this.gatherFormValues());
		}));
	}
});







