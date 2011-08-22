/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.quota");

dojo.require("umc.i18n");
dojo.require("umc.widgets.Module");

dojo.require("umc.modules._quota.OverviewPage");

dojo.declare("umc.modules.quota", [ umc.widgets.Module, umc.i18n.Mixin ], {

	_overviewPage: null,

	buildRendering: function() {
		this.inherited(arguments);

		this._overviewPage = new umc.modules._quota.OverviewPage({
			moduleStore: this.getModuleStore('id', this.moduleID + '/partitions'),

			headerText: this._('Filesystem quotas'),
			helpText: this._('Set, unset and modify filesystem quota')
		});

		this.addChild(this._overviewPage);
		this._overviewPage.startup();
    }
});
