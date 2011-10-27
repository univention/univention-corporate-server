/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._quota.PageContainer");

dojo.require("umc.i18n");
dojo.require("umc.store");

dojo.require("umc.modules._quota.PartitionPage");
dojo.require("umc.modules._quota.DetailPage");

dojo.declare("umc.modules._quota.PageContainer", [ dijit.layout.StackContainer, umc.i18n.Mixin ], {

	moduleID: null,
	partitionDevice: null,
	_partitionPage: null,
	_detailPage: null,

	buildRendering: function(partitionDevice) {
		this.inherited(arguments);
		this.renderPartitionPage();
		this.renderDetailPage();
	},

	postCreate: function() {
		this.inherited(arguments);
		this.selectChild(this._pageContainer);
	},

	renderPartitionPage: function() {
		this._partitionPage = new umc.modules._quota.PartitionPage({
			partitionDevice: this.partitionDevice,
			moduleStore: umc.store.getModuleStore('id', this.moduleID + '/users'),
			headerText: this._('Partition: %s', this.partitionDevice),
			helpText: this._('Set, unset and modify filesystem quota')
		});
		this.addChild(this._partitionPage);
		this.connect(this._partitionPage, 'onShowDetailPage', function(userQuota) {
			this._detailPage.init(userQuota);
			this.selectChild(this._detailPage);
		});
	},

	renderDetailPage: function() {
		this._detailPage = new umc.modules._quota.DetailPage({
			partitionDevice: this.partitionDevice,
			headerText: this._('Add quota setting for a user on partition'),
			helpText: this._('Add quota setting for a user on partition')
		});
		this.addChild(this._detailPage);
		this.connect(this._detailPage, 'onClosePage', function() {
			this.selectChild(this._partitionPage);
		});
		this.connect(this._detailPage, 'onSetQuota', function(values) {
			umc.tools.umcpCommand('quota/users/set', values).then(dojo.hitch(this, function(data) {
				if (data.result.success === true) {
					this.selectChild(this._partitionPage);
					this._partitionPage.filter();
				}
			}));
		});
	}
});
