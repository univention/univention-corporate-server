/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.TitlePane");

dojo.require("dijit.TitlePane");
dojo.require("dijit._Container");

dojo.declare("umc.widgets.TitlePane", [ dijit.TitlePane, dijit._Container ], {
	// summary:
	//		Widget that extends dijit.TitlePane with methods of a container widget.

	// the widget's class name as CSS class
	'class': 'umcTitlePane',

	startup: function() {
		this.inherited(arguments);

		// FIXME: Workaround for refreshing problems with datagrids when they are rendered
		//        in a closed TitlePane

		// iterate over all tabs
		dojo.forEach(this.getChildren(), function(ipage) {
			// find all widgets that inherit from dojox.grid._Grid on the tab
			dojo.forEach(ipage.getDescendants(), function(iwidget) {
				if (umc.tools.inheritsFrom(iwidget, 'dojox.grid._Grid')) {
					// hook to changes for 'open'
					this.watch('open', function(attr, oldVal, newVal) {
						if (newVal) {
							// recall startup when the TitelPane gets shown
							iwidget.startup();
						}
					});
				}
			}, this);
		}, this);
	}
});


