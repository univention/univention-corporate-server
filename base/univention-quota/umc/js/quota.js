/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.quota");

dojo.require("umc.i18n");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");

dojo.declare("umc.modules.quota", [ umc.widgets.Module, umc.i18n.Mixin ], {

	_grid: null,
	_store: null,
	_searchWidget: null,
	_contextVariable: null,
	_page: null,

	i18nClass: 'umc.modules.quota',

	buildRendering: function() {
		this.inherited(arguments);

		this._page = new umc.widgets.Page({
			headerText: this._('Filesystem quotas'),
			helpText: this._('Set, unset and modify filesystem quota')
		});

		this.addChild(this._page);

		this._page.startup();
    }
});
