/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.Module");

dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.tools");

dojo.declare("umc.widgets.Module", [ umc.widgets.Page, umc.widgets.StandbyMixin ], {
	// summary:
	//		Basis class for all module classes.

	flavor: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		// set the css class umcModulePane
		this['class'] = (this['class'] || '') + ' umcModulePane';
	},

	umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor ) {
		return umc.tools.umcpCommand( commandStr, dataObj, handleErrors, flavor || this.flavor );
	}

});


