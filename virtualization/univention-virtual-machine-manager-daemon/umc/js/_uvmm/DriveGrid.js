/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._uvmm.DriveGrid");

dojo.require("dijit.Dialog");

dojo.require("umc.tools");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Form");
dojo.require("umc.modules._uvmm.DriveWizard");

dojo.declare("umc.modules._uvmm.DriveGrid", [ umc.widgets.Grid, umc.i18n.Mixin ], {
	moduleStore: null,

	domain: null,

	i18nClass: 'umc.modules.uvmm',

	query: {},

	style: 'width: 100%; height: 150px;',

	constructor: function() {
		dojo.mixin(this, {
			columns: [{
				name: 'device',
				label: this._('Type'),
				formatter: dojo.hitch(this, function(dev) {
					return umc.modules._uvmm.types.blockDevices[dev] || this._('unknown');
				})
			}, {
				name: 'volumeFilename',
				label: this._('Image')
			}, {
				name: 'size',
				label: this._('Size')
			}, {
				name: 'pool',
				label: this._('Pool')
			}],
			actions: [{
			/*	name: 'delete',
				label: this._('Delete'),
				isMultiAction: true,
				isStandardAction: true,
				iconClass: 'umcIconDelete',
				callback: dojo.hitch(this, '_deleteSnapshots')
			}, {
				name: 'revert',
				label: this._('Revert'),
				isMultiAction: false,
				isStandardAction: true,
				callback: dojo.hitch(this, '_revertSnapshot')
			}, {*/
				name: 'add',
				label: this._('Add drive'),
				isMultiAction: false,
				isContextAction: false,
				iconClass: 'umcIconAdd',
				callback: dojo.hitch(this, '_addDrive')
			}]
		});
	},

	_addDrive: function() {
		var dialog = null, wizard = null;

		var _cleanup = function() {
			dialog.hide();
			dialog.destroyRecursive();
			wizard.destroyRecursive();
		};

		var _finished = dojo.hitch(this, function(values) {
			_cleanup();
			this.moduleStore.add(values);
		});

		wizard = new umc.modules._uvmm.DriveWizard({
			style: 'width: 450px; height:400px;',
			moduleStore: this.moduleStore,
			domain: this.domain,
			onFinished: _finished,
			onCancel: _cleanup
		});

		dialog = new dijit.Dialog({
			title: this._('Add a new drive'),
			content: wizard
		});
		dialog.show();
	},

	filter: function() {
		this.inherited(arguments, [{}]);
	},

	onUpdateProgress: function(i, n) {
		// event stub
	}
});
