/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Form");

dojo.require("dijit.form.Form");
dojo.require("dojox.form.manager._Mixin");
dojo.require("dojox.form.manager._ValueMixin");
dojo.require("dojox.form.manager._EnableMixin");
dojo.require("dojox.form.manager._DisplayMixin");
dojo.require("dojox.form.manager._ClassMixin");
dojo.require("umc.widgets.Tooltip");
dojo.require("umc.tools");

dojo.declare("umc.widgets.Form", [
		dijit.form.Form,
		dojox.form.manager._Mixin,
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

	// orient: String
	//		Orientation of labels, possible values ['vert', 'horiz'].
	orientation: 'vert',

	// umcpGet: String
	//		UMCP command for querying data to fill the form.
	umcpGetCommand: '',

	// umcpSet: String
	//		UMCP command for saving data from the form.
	umcpSetCommand: '',

	_widgets: null,

	_buttons: null,

	_layoutContainer: null,

	'class': 'umcNoBorder',

	buildRendering: function() {
		this.inherited(arguments);

		// render the widgets and the layout
		this._widgets = umc.tools.renderWidgets(this.widgets);
		this._buttons = umc.tools.renderButtons(this.buttons);
		this._layoutContainer = umc.tools.renderLayout(this.layout, this._widgets, this._buttons, {
			cols: this.cols,
			orientation: this.orientation
		});

		// register tooltips
		umc.tools.forIn(this._widgets, function(iname, iwidget) {
			// only create a tooltip if there is a description
			if (iwidget.description) {
				var tooltip = new umc.widgets.Tooltip({
					label: iwidget.description,
					connectId: [ iwidget.domNode ]
				});
			}
		}, this);

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
	},

	umcpGet: function(/*Object*/ parameters) {
		// summary:
		//		Send off an UMCP query to the server for querying the data for the form.
		//		For this the field umcpGetCommand needs to be set.
		// parameters: Object
		//		Parameter object that is passed to the UMCP command.

		umc.tools.assert(this.umcpGetCommand, 'In order to query form data from the server, umcpGetCommand needs to be set');

		// query data from server
		umc.tools.umcpCommand(this.umcpGetCommand, parameters).then(dojo.hitch(this, function(_data) {
			var values = this.gatherFormValues();
			var data = dojo.mixin({}, parameters, _data.result);
			var newValues = {};

			// copy all the fields that exist in the form
			umc.tools.forIn(data, function(ikey, ival) {
				if (ikey in values) {
					newValues[ikey] = ival;
				}
			}, this);

			// set all values at once
			this.setFormValues(newValues);

			// fire event
			this.onUmcpGetDone(true);
		}), dojo.hitch(this, function(error) {
			// fore event also in error case
			this.onUmcpGetDone(false);
		}));
	},

	umcpSet: function() {
		// summary:
		//		Gather all form values and send them to the server via UMCP.
		//		For this, the field umcpSetCommand needs to be set.

		umc.tools.assert(this.umcpSetCommand, 'In order to query form data from the server, umcpGetCommand needs to be set');

		// sending the data to the server
		var values = this.gatherFormValues();
		//TODO: parameter for UMCP set command should be an array
		var tmp = {};
		tmp[values.variable] = values.value;
		umc.tools.umcpCommand(this.umcpSetCommand, tmp).then(dojo.hitch(this, function(data) {
			// fire event
			this.onUmcpSetDone(true);
		}), dojo.hitch(this, function(error) {
			// fore event also in error case
			this.onUmcpSetDone(false);
		}));
	},

	onUmcpSetDone: function() {
		// event stub
	},

	onUmcpGetDone: function() {
		// event stub
	}
});







