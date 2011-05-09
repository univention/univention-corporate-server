/*global location dojo dijit dojox overview umc2 OverviewWidget ContainerPane */

dojo.registerModulePath( "umc2", location.href + "/umc2" );
dojo.registerModulePath( "umc", "/umc/umc" );

// load our modules
dojo.require("umc2.modules");
dojo.require("umc2.widgets");
dojo.require("umc2.app");

dojo.addOnLoad(function() {
	umc2.app.start();
});
