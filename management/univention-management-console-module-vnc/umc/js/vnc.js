/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.vnc");

dojo.require("umc.i18n");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");

dojo.declare("umc.modules.vnc", [ umc.widgets.Module, umc.i18n.Mixin ], {

	moduleStore: null,
	_page: null,

	buildRendering: function() {
		this.inherited(arguments);

		this._page = new umc.widgets.Page({
			headerText: this._('VNC')
		});
		this.addChild(this._page);

		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('VNC configuration')
		});
		this._page.addChild(titlePane);

		this._page.startup();
    }
});
