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

});


