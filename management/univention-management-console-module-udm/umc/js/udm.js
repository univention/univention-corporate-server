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
dojo.require("umc.widgets.SearchForm");

dojo.declare("umc.modules.udm", [ umc.widgets.Module, umc.i18n.Mixin ], {
	// summary:
	//		Module for handling UDM modules

	buildRendering: function() {
		// call superclass method
		this.inherited(arguments);

		// we need to dynamically load the search widget
		this.umcpCommand('udm/query/layout').then(dojo.hitch(this, function(data) {
			// add to each widget a reference to the module specific umcpCommand method
			var widgets = data.result;
			dojo.forEach(widgets, dojo.hitch(this, function(iwidget) {
				iwidget.umcpCommand = this.umcpCommand;
			}));

			// create the search widget
			this._searchWidget = new umc.widgets.SearchForm({
				region: 'top',
				widgets: widgets
			});
			this.addChild(this._searchWidget);
			this._layoutContainer.layout();
		}));
	}

});

