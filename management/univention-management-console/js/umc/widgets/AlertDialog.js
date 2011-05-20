/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.AlertDialog");

dojo.require("dijit.Dialog");
dojo.require("dojox.layout.TableContainer");
dojo.require("dojox.widget.Dialog");
dojo.require("umc.widgets.Label");

dojo.declare('umc.widgets.AlertDialog', dijit.Dialog, {
	// message: String
	//		The message to be displayed.
	message: '',

	// internal varialbles
	_labelWidget: null,

	_setMessageAttr: function(message) {
		this.message = message;
		this._labelWidget.set('content', message);
	},

	buildRendering: function() {
		this.inherited(arguments);

		// create our widgets
		this._labelWidget = umc.widgets.Label({
			content: this.message
		});
		var okButton = umc.widgets.Button({
			label: 'Ok',
			onClick: dojo.hitch(this, function(values) {
				this.hide();
			})
		});

		// put the layout together
		var layout = new dojox.layout.TableContainer({
			cols: 1,
			showLabels: false
		});
		layout.addChild(this._labelWidget);
		layout.addChild(okButton);
		layout.startup();
	
		// center button
		dojo.style(okButton.domNode.parentNode, 'textAlign', 'center');
		
		// attach layout to dialog
		this.set('content', layout);
	},

	postCreate: function() {
		this.inherited(arguments);
	}
});


