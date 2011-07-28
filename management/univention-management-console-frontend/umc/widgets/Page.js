/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.Page");

dojo.require("umc.app");
dojo.require("umc.widgets.Text");
dojo.require("umc.widgets.ContainerWidget");

dojo.declare("umc.widgets.Page", umc.widgets.ContainerWidget, {
	// summary:
	//		Class that abstracts a displayable page for a module.
	//		Offers the possibility to enter a help text that is shown or not
	//		depending on the user preferences.
	//		The widget itself is also a container such that children widgets
	//		may be adde via the 'addChild()' method.

	// helpText: String
	//		Text that describes the module, will be displayed at the top of a page.
	helpText: '',

	// title: String
	//		Title of the page. This option is necessary for tab pages.
	title: '',

	scrollable: true,

	_helpTextPane: null,
	_helpTextShown: true,
	_subscriptionHandle: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		// remove title from the attributeMap
		delete this.attributeMap.title;

		// get user preferences for the module helpText
		this._helpTextShown = umc.tools.preferences('moduleHelpText');
	},

	buildRendering: function() {
		this.inherited(arguments);

		// put the help text in a Text widget and then add it to the container
		this._helpTextPane = new umc.widgets.Text({
			content: this.helpText || '',
			'class': 'umcPageHelpText'
		});
		this.addChild(this._helpTextPane);

		// hide the help text if specified
		if (!this._helpTextShown) {
			dojo.style(this._helpTextPane.domNode, {
				opacity: 0,
				display: 'none'
			});
		}
	},

	postCreate: function() {
		this.inherited(arguments);

		// register for events to hide the help text information
		this._subscriptionHandle = dojo.subscribe('/umc/preferences/moduleHelpText', dojo.hitch(this, function(show) {
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

	showDescription: function() {
		// if we don't have a help text, ignore call
		if (!this._helpTextPane || this._helpTextShown) {
			return;
		}

		// make the node transparent, yet displayable
		dojo.style(this._helpTextPane.domNode, {
			opacity: 0,
			display: 'block'
		});
		this._helpTextShown = true;

		// fade in the help text
		dojo.fadeIn({
			node: this._helpTextPane.domNode,
			duration: 500
		}).play();
	},

	hideDescription: function() {
		// if we don't have a help text or the help text is already hidden, ignore call
		if (!this._helpTextPane || !this._helpTextShown) {
			return;
		}

		// fade out the help text
		dojo.fadeOut({
			node: this._helpTextPane.domNode,
			duration: 500,
			onEnd: dojo.hitch(this, function() {
				this._helpTextShown = false;
				dojo.style(this._helpTextPane.domNode, {
					display: 'none'
				});
			})
		}).play();
	}
});


