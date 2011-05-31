/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.udm");

dojo.require("umc.widgets.Module");
dojo.require("umc.tools");
/*dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.ContainerForm");
dojo.require("umc.widgets.StandbyMixin");*/
dojo.require("umc.i18n");

dojo.declare("umc.modules.udm", [ umc.widgets.Module, umc.i18n.Mixin ], {
	// summary:
	//		Module for handling UDM modules

	_grid: null,
	_store: null,
	_searchWidget: null,
	_detailDialog: null,
	_contextVariable: null,

	buildRendering: function() {
		// call superclass method
		this.inherited(arguments);


	}

});

