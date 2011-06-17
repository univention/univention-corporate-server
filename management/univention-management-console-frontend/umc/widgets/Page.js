/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.Page");

dojo.require("dijit.layout.ContentPane");
dojo.require("dijit.layout.BorderContainer");
dojo.require("umc.app");

dojo.declare("umc.widgets.Page", dijit.layout.ContentPane, {
	// summary:
	//		Class that abstracts a displayable page for a module.
	//		Offers a BorderContainer for layout.

	// description: String
	//		Text that describes the module, will be displayed at the top of a page.
	description: '',

	_layoutContainer: null,
	_topLayoutContainer: null,
	_descriptionPane: null,
	_descriptionShown: true,
	_subscriptionHandle: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		// get user preferences for the module description
		this._descriptionShown = umc.app.preferences('moduleDescription');
	},

	buildRendering: function() {
		this.inherited(arguments);
		
		// in case we have a description, put it into the layout ... it needs to
		// be displayed at the very top, therefor use a container in a container
		if (this.description) {
			// create a content pane for the module description
			this._descriptionPane = new dijit.layout.ContentPane({
				content: this.description,
				region: 'top',
				gutters: false,
				'class': 'umcNoBorder umcNoPadding'
			});

			// hide the description if specified
			if (!this._descriptionShown) {
				dojo.style(this._descriptionPane.domNode, {
					opacity: 0,
					display: 'none'
				});
			}

			// put everything together
			this._topLayoutContainer = new dijit.layout.BorderContainer({});
			this._topLayoutContainer.addChild(this._descriptionPane);
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

	postCreate: function() {
		this.inherited(arguments);

		// register for events to hide the description information
		this._subscriptionHandle = dojo.subscribe('/umc/preferences/moduleDescription', dojo.hitch(this, function(show) {
			if (false === show) {
				this.hideDescription();
			}
			else {
				this.showDescription();
			}
		}));
	},

	uninitialize: function() {
		// unsubscribe upon destruction
		dojo.unsubscribe(this._subscriptionHandle);
	},

	addChild: function(item) {
		this._layoutContainer.addChild(item);
	},

	startup: function() {
		var container = this._topLayoutContainer || this._layoutContainer;
		container.startup();
	},

	showDescription: function() {
		// if we don't have a description, ignore call
		if (!this._descriptionPane || this._descriptionShown) {
			return;
		}

		// make the node transparent, yet displayable and redo the layout
		dojo.style(this._descriptionPane.domNode, {
			opacity: 0,
			display: 'block'
		});
		this.layout();
		this._descriptionShown = true;
		
		// fade in the description
		dojo.fadeIn({
			node: this._descriptionPane.domNode,
			duration: 500
		}).play();
	},

	hideDescription: function() {
		// if we don't have a description or the description is already hidden, ignore call
		if (!this._descriptionPane || !this._descriptionShown) {
			return;
		}
		
		// fade out the description
		dojo.fadeOut({
			node: this._descriptionPane.domNode,
			duration: 500,
			onEnd: dojo.hitch(this, function() {
				// redo the layout
				this._descriptionShown = false;
				dojo.style(this._descriptionPane.domNode, {
					display: 'none'
				});
				this.layout();
			})
		}).play();
	},

	layout: function() {
		var container = this._topLayoutContainer || this._layoutContainer;
		container.layout();
	}
});


