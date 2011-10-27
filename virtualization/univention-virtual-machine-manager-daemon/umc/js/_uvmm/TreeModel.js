/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._uvmm.TreeModel");

dojo.require("umc.tools");

dojo.declare('umc.modules._uvmm.TreeModel', null, {
	// summary:
	//		Class that implements the tree model for the UVMM navigation hierarchy.

	// umcpCommand: Function
	//		Reference to the module specific umcpCommand function.
	umcpCommand: null,

	// root: Object
	//		A dummy root node.
	root: null,

	constructor: function(args) {
		dojo.mixin(this, args);
	
		this.root = {
			id: '$root$',
			label: 'Univention Virtual Machine Manager',
			type: 'root'
		};
	},

	getRoot: function(onItem) {
		onItem(this.root);
	},

	getLabel: function(item) {
		return item.label;
	},

	mayHaveChildren: function(item) {
		if (!item.type || item.type == 'node') {
			return false;
		}
		return true;
	},

	getIdentity: function(item) {
		return item.id;
	},

	getChildren: function(parentItem, onComplete) {
		if (!parentItem.type || parentItem.type == 'node') {
			onComplete([]);
			return
		}

		this.umcpCommand('uvmm/nav/query', { 
			parent: parentItem.type == 'root' ? null : parentItem
		}).then(dojo.hitch(this, function(data) {
			// sort items alphabetically
			var results = dojo.isArray(data.result) ? data.result : [];
			results.sort(umc.tools.cmpObjects('label'));
			onComplete(results);
		}));
	}
});



