/*global dojo dijit dojox umc console clearTimeout */

dojo.provide("umc.widgets.Tree");

dojo.require("dijit.Tree");

dojo.declare("umc.widgets.Tree", dijit.Tree, {
	// summary:
	//		Extension of `dijit.Tree` with a `refresh()` method.
	// description:
	//		This code has been imported from: http://bugs.dojotoolkit.org/ticket/11065

	// the widget's class name as CSS class
	'class': 'umcTree',

	/** 
	 * Unset tree's attributes but leave the widget untouched. 
	 * This code is copied from dijit.Tree's .destroy()-method. 
	 * 
	 * dijit.Tree.destroy() could be reduced to 
	 * 
	 * destroy: function() {
	 * 		this._destroy();
	 * 		this.inherited(arguments);
	 * }
	 * 
	 * if someone of the dijit.Tree-developers can 
	 * implement this ._destroy()-method.
	 *  
	 **/
	_destroy: function(){
		if(this._curSearch){
			clearTimeout(this._curSearch.timer);
			delete this._curSearch;
		}
		if(this.rootNode){
			this.rootNode.destroyRecursive();
		}
		if(this.dndController && !dojo.isString(this.dndController)){
			this.dndController.destroy();
		}
		this.rootNode = null;
	},

	/**
	 * reload the whole tree
	 *  
	 * (many thanks to the tips from Rob Weiss found here: 
	 * http://mail.dojotoolkit.org/pipermail/dojo-interest/2010-April/045180.html)
	 */
	reload: function () {
		/* remember current paths: 
		 * simplify all nodes of paths-array to strings of identifiers because 
		 * after reload the nodes may have different ids and therefore the 
		 * paths may not be applied */ 
		var reloadPaths = dojo.map(this.get('paths'), dojo.hitch(this, function(path) {
			return dojo.map(path, dojo.hitch(this, function(pathItem) {
				return this.model.getIdentity(pathItem) + '';
			}));
		}));
		
		/* reset tree: */
		this._destroy();
		this.dndController = "dijit.tree._dndSelector";
		
		/* unset the store's cache (if existing).  
		 * TODO: currently only tested on JsonRestStore! */ 
		if (dojox && dojox.rpc && dojox.rpc.Rest && dojox.rpc.Rest._index) {
			for (var idx in dojox.rpc.Rest._index) {
				if (idx.match("^" + this.model.store.target)) {
					delete dojox.rpc.Rest._index[idx];
				}
			}
		}

		// reset the tree.model's root
		this.model.constructor({
			rootId: '0',
			rootLabel: ''
		});
		
		// rebuild the tree
		this.postMixInProperties();
		this.postCreate();
		
		/* reset the paths */
		this._reloadOnLoadConnect = dojo.connect(this, 'onLoad', dojo.hitch(this, function() {
			/* restore old paths.   
			 * FIXME: this will result in an error if a formerly selected item 
			 * is no longer existent in the tree after reloading! */
			this.set('paths', reloadPaths).then(dojo.hitch(this, function() {
				if (this.get('selectedNode')) {
					this.focusNode(this.get('selectedNode'));
				}
				dojo.disconnect(this._reloadOnLoadConnect);
				this._reloadOnLoadConnect = null;
			}));
		}));
	}	
});



