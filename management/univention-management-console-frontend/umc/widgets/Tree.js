/*
 * Copyright 2011-2015 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global define clearTimeout*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dijit/Tree"
], function(declare, lang, array, Tree) {
	return declare("umc.widgets.Tree", Tree, {
		// summary:
		//		Extension of `dijit.Tree` with a `refresh()` method.
		// description:
		//		This code has been imported from: http://bugs.dojotoolkit.org/ticket/11065

		'class': 'umcDynamicHeight',

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
			if(this.dndController && typeof this.dndController != "string"){
				this.dndController.destroy();
			}
			this.rootNode = null;
		},

		resize: function() {
			//console.log('### Tree.resize');
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
			var reloadPaths = array.map(this.get('paths'), lang.hitch(this, function(path) {
				return array.map(path, lang.hitch(this, function(pathItem) {
					return this.model.getIdentity(pathItem) + '';
				}));
			}));

			/* reset tree: */
			this._destroy();
			this.dndController = "dijit.tree._dndSelector";

			/* unset the store's cache (if existing).
			 * TODO: currently only tested on JsonRestStore! */
			/*if (dojox && dojox.rpc && dojox.rpc.Rest && dojox.rpc.Rest._index) {
				for (var idx in dojox.rpc.Rest._index) {
					if (idx.match("^" + this.model.store.target)) {
						delete dojox.rpc.Rest._index[idx];
					}
				}
			}*/

			// reset the tree.model's root
			this.model.constructor({
				rootId: '0',
				rootLabel: ''
			});

			// rebuild the tree
			this.postMixInProperties();
			this.postCreate(); // FIXME: this registers events again

			/* reset the paths */
			this._reloadOnLoadConnect = this.on('load', lang.hitch(this, function() {
				/* restore old paths.
				 * FIXME: this will result in an error if a formerly selected item
				 * is no longer existent in the tree after reloading! */
				this.set('paths', reloadPaths).then(lang.hitch(this, function() {
					if (this.get('selectedNode')) {
						this.focusNode(this.get('selectedNode'));
					}
					this._reloadOnLoadConnect.remove();
					this._reloadOnLoadConnect = null;
				}));
			}));
		}
	});
});


