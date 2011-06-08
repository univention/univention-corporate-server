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

	buildRendering: function() {
		// call superclass method
		this.inherited(arguments);
		this.umcpCommand( 'udm/search/properties' ).then( dojo.hitch( this, function ( umcpResponse ) {
																		  // define all buttons
																		  var buttons = [{
																							 name: 'submit',
																							 label: this._( 'Search' ),
																							 callback: dojo.hitch(this._grid, 'umcpSearch')
																						 }, {
																							 name: 'reset',
																							 label: this._( 'Reset' )
																						 }];

																		  // define the search form layout
																		  var layout = [
																			  [ 'category', '' ],
																			  [ 'key', 'filter' ]
																		  ];

																		  var widgets = umcpResponse.result;

																		  // generate the search widget
																		  this._searchWidget = new umc.widgets.Form({
																														region: 'top',
																														widgets: widgets,
																														buttons: buttons,
																														layout: layout
																													});
																		  this.addChild(this._searchWidget);
																		  } ), null );
	}

});

