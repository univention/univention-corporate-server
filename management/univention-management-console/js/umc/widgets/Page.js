/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.Page");

dojo.require("dijit.layout.ContentPane");
dojo.require("dijit.layout.BorderContainer");

dojo.declare("umc.widgets.Page", dijit.layout.ContentPane, {
	// summary:
	//		Class that abstracts a displayable page for a module.
	//		Offers a BorderContainer for layout.

	// description: String
	//		Text that describes the module, will be displayed at the top of a page.
	description: '',

	_layoutContainer: null,

	buildRendering: function() {
		this.inherited(arguments);
		
		// in case we have a description, put it into the layout ... it needs to
		// be displayed at the very top, therefor use a container in a container
		if (this.description) {
			this._topLayoutContainer = new dijit.layout.BorderContainer({});
			this._topLayoutContainer.addChild(new dijit.layout.ContentPane({
				content: this.description,
				region: 'top',
				gutters: false,
				'class': 'umcNoBorder umcNoPadding'
			}));
			this._layoutContainer = new dijit.layout.BorderContainer({
				region: 'center'
			});
			this._topLayoutContainer.addChild(this._layoutContainer);
			this.content = this._topLayoutContainer;
		}
		// otherwise simply create one BorderContainer for the layout
		else {
			this._layoutContainer = new dijit.layout.BorderContainer({});
			this.content = this._layoutContainer;
		}
	},

	addChild: function(item) {
		this._layoutContainer.addChild(item);
	},

	startup: function() {
		var container = this._topLayoutContainer || this._layoutContainer;
		container.startup();
	},

	standby: function() { }
	
});


