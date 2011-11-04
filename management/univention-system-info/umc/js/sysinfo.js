/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.sysinfo");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.widgets.Module");

dojo.declare("umc.modules.services", [ umc.widgets.Module, umc.i18n.Mixin ], {

	buildRendering: function() {
		this.inherited(arguments);
	}
});
