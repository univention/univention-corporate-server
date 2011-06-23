/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.ConfirmDialog");

dojo.require("dijit.Dialog");
dojo.require("dojox.layout.TableContainer");
dojo.require("dojox.widget.Dialog");
dojo.require("umc.tools");
dojo.require("umc.widgets.Text");
dojo.require("umc.widgets.ContainerWidget");

dojo.declare('umc.widgets.ConfirmDialog', dijit.Dialog, {
	// message: String
	//		The message to be displayed.
	message: '',

	// options: Object
	//		Array with all available choices (buttons). Each entry must have the
	//		property 'label' and may have a 'callback', i.e., a user specified
	//		function that is called. The callback will receive as parameter the
	//		option chosen, i.e., an integer or - if specified - the corresponding
	//		'name' property of the button.
	options: [],

	// our own settings
	closable: false,

	// internal varialbles
	_labelWidget: null,

	_setMessageAttr: function(message) {
		this.message = message;
		this._labelWidget.set('content', message);
	},

	buildRendering: function() {
		this.inherited(arguments);

		// create our widgets...
		this._labelWidget = umc.widgets.Text({
			content: this.message
		});
		
		// put buttons into separate container
		var buttons = new umc.widgets.ContainerWidget({});
		dojo.forEach(this.options, dojo.hitch(this, function(ichoice, idx) {
			buttons.addChild(new umc.widgets.Button({
				label: ichoice.label,
				onClick: dojo.hitch(this, function(values) {
					// the response is either a custom response or the choice (button) index
					var response = ichoice.name || idx; 

					// send 'onClick' event
					this.onConfirm(response);

					// call custom callback if specified
					if (ichoice.callback) {
						ichoice.callback(response);
					}
				})
			}));
		}));

		// put the layout together
		var layout = new dojox.layout.TableContainer({
			cols: 1,
			showLabels: false
		});
		layout.addChild(this._labelWidget);
		layout.addChild(buttons);
		layout.startup();
	
		// center buttons
		dojo.style(buttons.domNode.parentNode, 'textAlign', 'center');
		
		// attach layout to dialog
		this.set('content', layout);
	},

	postCreate: function() {
		this.inherited(arguments);
	},

	close: function() {
		// summary:
		//		Hides the dialog and destroys it after the fade-out animation.
		this.hide().then(dojo.hitch(this, function() {
			this.destroyRecursive();
		}));
	},

	onConfirm: function(/*String*/ choice) {
		// summary:
		//		Event that is fired when the user confirms the dialog
		//		either with true or false.
		// choice:
		//		The key of option that has been chosen.
	}
});


