/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.adconnector");

dojo.require("umc.i18n");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");

dojo.declare("umc.modules.adconnector", [ umc.widgets.Module, umc.i18n.Mixin ], {

	standbyOpacity: 1.00,

	_widgets: null,

	_buttons: null,

	buildRendering: function() {
		this.inherited(arguments);
		this.standby(true);

		var widgets = [
			{
				name: 'configured',
				type: 'Text'
			}, {
				name: 'certificate',
				type: 'Text'
			}, {
				name: 'running',
				type: 'Text'
			}
		];
		var buttons = [
			{
				name: 'start',
				label: this._( 'Start AD connector' ),
				callback: dojo.hitch( this, function() {
					umc.tools.umcpCommand( 'adconnector/service', { action : 'start' } ).then( dojo.hitch( this, function( response ) {
						this.hideShowElements();
					} ) );
				} )
			}, {
				name: 'stop',
				label: this._( 'Stop AD connector' ),
				callback: dojo.hitch( this, function() {
					umc.tools.umcpCommand( 'adconnector/service', { action : 'stop' } ).then( dojo.hitch( this, function( response ) {
						this.hideShowElements();
					} ) );
				} )
			}, {
				name: 'configure',
				label: this._( 'Configure AD connector' ),
				callback: dojo.hitch( this, function() {
					umc.tools.umcpCommand( 'adconnector/service', { action : 'stop' } ).then( dojo.hitch( this, function( response ) {
						this.hideShowElements();
					} ) );
				} )
			}
		];

		this._widgets = umc.render.widgets( widgets );
		this._buttons = umc.render.widgets( buttons );

		var _container = umc.render.layout( [ 'configured', 'certificate', 'running', 'start', 'stop', 'configure' ], this._widgets, this._buttons );
		this.addChild( _container );
    },

	showHideElements: function() {
	}
} );