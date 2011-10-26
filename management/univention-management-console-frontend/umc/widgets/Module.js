/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.Module");

dojo.require("dijit.layout.StackContainer");
dojo.require("umc.widgets._ModuleMixin");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.widgets.Module", [ dijit.layout.StackContainer, umc.widgets._ModuleMixin, umc.widgets.StandbyMixin ], {
	// summary:
	//		Basis class for module classes.
	//		It extends dijit.layout.StackContainer and adds some module specific
	//		properties/methods.

	// initial title set for the module
	defaultTitle: null,

	postMixInProperties: function() {
		this.inherited(arguments);
		this.defaultTitle = this.title;
	},

	resetTitle: function() {
		this.set( 'title', this.defaultTitle );
	},

	startup: function() {
		this.inherited(arguments);

		// FIXME: Workaround for refreshing problems with datagrids when they are rendered
		//        on an inactive tab.

		// iterate over all tabs
		dojo.forEach(this.getChildren(), function(ipage) {
			// find all widgets that inherit from dojox.grid._Grid on the tab
			dojo.forEach(ipage.getDescendants(), function(iwidget) {
				if (umc.tools.inheritsFrom(iwidget, 'dojox.grid._Grid')) {
					// hook to onShow event
					this.connect(ipage, 'onShow', function() {
						iwidget.startup();
					});
				}
			}, this);
		}, this);
	}
});


