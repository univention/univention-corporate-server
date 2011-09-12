/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.TabbedModule");

dojo.require("umc.widgets.TabContainer");
dojo.require("umc.widgets._ModuleMixin");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.widgets.TabbedModule", [ umc.widgets.TabContainer, umc.widgets._ModuleMixin, umc.widgets.StandbyMixin ], {
	// summary:
	//		Basis class for module classes.
	//		It extends dijit.layout.TabContainer and adds some module specific
	//		properties/methods.

	// subtabs should be displayed as nested tabs
	nested: true
});


