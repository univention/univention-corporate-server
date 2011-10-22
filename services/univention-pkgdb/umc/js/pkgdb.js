/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.pkgdb");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.widgets.TabbedModule");

dojo.require("umc.modules._pkgdb.Page");


dojo.declare("umc.modules.pkgdb", [ umc.widgets.TabbedModule, umc.i18n.Mixin ], {
	
	i18nClass:		'umc.modules.pkgdb',
	
	buildRendering: function() {
		this.inherited(arguments);
			
		var syspage = new umc.modules._pkgdb.Page({
			title:			this._("Systems"),
			headerText:		this._("Search systems"),
			helpText:		this._("Search for systems with specific software properties"),
			pageKey:		'systems'
		});
		this.addChild(syspage);

		var packpage = new umc.modules._pkgdb.Page({
			title:			this._("Packages"),
			headerText:		this._("Search packages"),
			helpText:		this._("Search for packages with specific software properties"),
			pageKey:		'packages'
		});
		this.addChild(packpage);
		
		var propage = new umc.modules._pkgdb.Page({
			title:			this._("Problems"),
			headerText:		this._("Identify problems"),
			helpText:		this._("Find problems related to software package installation"),
			pageKey:		'problems'
		});
		this.addChild(propage);
		
	}
	
//	startup: function() {
//		
//		this.inherited(arguments);
//		
//	},
//	
//	uninitialize: function() {
//		
//		this.inherited(arguments);
//		this._refresh_time = 0;
//		
//	}
	
});
