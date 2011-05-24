/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.Module");

dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.widgets.Module", [ umc.widgets.Page, umc.widgets.StandbyMixin ], {
	// summary:
	//		Basis class for all module classes.

	postMixInProperties: function() {
		this.inherited(arguments);

		// set the css class umcModulePane
		this['class'] = (this['class'] || '') + ' umcModulePane';
	}
});


