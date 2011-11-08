/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._uvmm.InterfaceGrid");

dojo.require("dijit.Dialog");

dojo.require("umc.tools");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Form");

dojo.declare("umc.modules._uvmm.InterfaceGrid", [ umc.widgets.Grid, umc.i18n.Mixin ], {
	i18nClass: 'umc.modules.uvmm',

	query: {},

	style: 'width: 100%; height: 200px;',

	constructor: function() {
		dojo.mixin(this, {
			columns: [{
				name: 'type',
				label: this._('Type')
			}, {
				name: 'source',
				label: this._('Source')
			}, {
				name: 'model',
				label: this._('Driver'),
				formatter: dojo.hitch(this, function(model) {
					return umc.modules._uvmm.types.interfaceModels[model] || this._('unknown');
				})
			}, {
				name: 'mac_address',
				label: this._('MAC address')
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
