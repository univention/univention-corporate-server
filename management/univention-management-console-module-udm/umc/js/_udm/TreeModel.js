/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._udm.TreeModel");

dojo.require("umc.tools");

dojo.declare('umc.modules._udm.TreeModel', null, {
	// summary:
	//		Class that implements the tree model for the UDM container hierarchy.
	// summary:
	//		This class that implements a tree model for the container hierarchy which
	//		is use in the UDM navigation module in combination with the diji.Tree widget.
	//		More details about this model can be found in dijit.tree.model.

	// umcpCommand: Function
	//		Reference to the module specific umcpCommand function.
	umcpCommand: null,

	root: null,

	constructor: function(args) {
		dojo.mixin(this, args);
	},

	getRoot: function(onItem) {
		this.umcpCommand('udm/nav/container/query').then(dojo.hitch(this, function(data) {
			var results = dojo.isArray(data.result) ? data.result : [];
			if (results.length) {
				onItem(results[0]);
				this.root = results[0];
			}
			else {
				console.log('WARNING: No top container could be queried for LDAP navigation! Ignoring error.');
			}
		}));
	},

	getLabel: function(item) {
		return item.label;
	},

	mayHaveChildren: function(item) {
		return true;
	},

	getIdentity: function(item) {
		return item.id;
	},

	getChildren: function(parentItem, onComplete) {
		this.umcpCommand('udm/nav/container/query', { container: parentItem.id }).then(dojo.hitch(this, function(data) {
			// sort items alphabetically
			var results = dojo.isArray(data.result) ? data.result : [];
			results.sort(umc.tools.cmpObjects('label'));
			try {
				onComplete(results);
			}
			catch (error) {
				// don't do anything
			}
		}));
	}
});



