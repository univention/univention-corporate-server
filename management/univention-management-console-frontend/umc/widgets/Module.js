/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.Module");

dojo.require("umc.widgets._ModuleMixin");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.tools");

dojo.declare("umc.widgets.Module", [ umc.widgets.Page, umc.widgets.StandbyMixin, umc.widgets._ModuleMixin ], {
	// summary:
	//		Basis class for all module classes.

	postMixInProperties: function() {
		this.inherited(arguments);

		// initated the _ModuleMixin class
		this._moduleInit();

		// set the css class umcModulePane
		this['class'] = (this['class'] || '') + ' umcModulePane';
	}

});


