/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.ConfirmDialog");

dojo.require("dijit.Dialog");
dojo.require("dojox.layout.TableContainer");
dojo.require("dojox.widget.Dialog");
dojo.require("umc.tools");
dojo.require("umc.widgets.Label");
dojo.require("umc.widgets.ContainerWidget");

dojo.declare('umc.widgets.ConfirmDialog', dijit.Dialog, {
	// message: String
	//		The message to be displayed.
	message: '',

	// options: Object
	//		Dictionary with id-label pairs for all available options.
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
		this._labelWidget = umc.widgets.Label({
			content: this.message
		});
		
		// put buttons into separate container
		var buttons = new umc.widgets.ContainerWidget({});
		umc.tools.forIn(this.options, dojo.hitch(this, function(val, key) {
			buttons.addChild(new umc.widgets.Button({
				label: val,
				onClick: dojo.hitch(this, function(values) {
					this.onConfirm(key);
					this.close();
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


