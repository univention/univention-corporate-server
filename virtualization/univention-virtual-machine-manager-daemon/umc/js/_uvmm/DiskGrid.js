/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._uvmm.DiskGrid");

dojo.require("dijit.Dialog");

dojo.require("umc.tools");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Form");

dojo.declare("umc.modules._uvmm.DiskGrid", [ umc.widgets.Grid, umc.i18n.Mixin ], {
	i18nClass: 'umc.modules.uvmm',

	query: {},

	style: 'width: 100%; height: 200px;',

	constructor: function() {
		dojo.mixin(this, {
			columns: [{
				name: 'device',
				label: this._('Type'),
				formatter: dojo.hitch(this, function(dev) {
					return umc.modules._uvmm.types.blockDevices[dev] || this._('unknown');
				})
			}, {
				name: 'source',
				label: this._('Image'),
				formatter: function(source) {
					var list = source.split('/');
					if (list.length) {
						return list[list.length - 1];
					}
					return this._('unknown');
				}
			}, {
				name: 'size',
				label: this._('Size'),
				formatter: function(size) {
					return dojox.string.sprintf('%.1f GB', size / 1073741824.0);
				}
			}, {
				name: 'pool',
				label: this._('Pool')
			}]/*,
			actions: [{
				name: 'delete',
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
			}, {
				name: 'add',
				label: this._('Create new snapshot'),
				isMultiAction: false,
				isContextAction: false,
				iconClass: 'umcIconAdd',
				callback: dojo.hitch(this, '_addSnapshot')
			}]*/
		});
	},

	filter: function() {
		this.inherited(arguments, [{}]);
	},

	onUpdateProgress: function(i, n) {
		// event stub
	}
});
