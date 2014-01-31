/*
 * Copyright 2011-2014 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, tools, _) {

	return declare('umc.modules.uvmm.TreeModel', null, {
		// summary:
		//		Class that implements the tree model for the UVMM navigation hierarchy.

		// umcpCommand: Function
		//		Reference to the module specific umcpCommand function.
		umcpCommand: null,

		// root: Object
		//		A dummy root node.
		root: null,

		constructor: function(args) {
			lang.mixin(this, args);

			this.root = {
				id: '$root$',
				label: 'UCS Virtual Machine Manager',
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
			return item.type != 'domain';
		},

		getIdentity: function(item) {
			return item.id;
		},

		_cutDomain: function( fqdn ) {
			var dot = fqdn.indexOf( '.' );
			if ( dot != -1 ) {
				return fqdn.substr( 0, dot );
			}
			return fqdn;
		},

		getChildren: function(parentItem, onComplete) {
			// we only have three levels: root, groups, nodes
			if (parentItem.type == 'node') {
				onComplete([]);
				return;
			}

			this.umcpCommand('uvmm/query', {
				type: parentItem.type == 'root' ? 'group' : 'node',
				domainPattern: '*',
				nodePattern: '*'
			}).then(lang.hitch(this, function(data) {
				// sort items alphabetically
				var results = data.result instanceof Array ? data.result : [];
				results.sort(tools.cmpObjects('label'));
				onComplete( array.map( results, lang.hitch( this, function( node ) {
					// cut off domain name
					node.label = this._cutDomain( node.label );
					return node;
				} ) ) );
			}));
		},

		changes: function( nodes ) {
			array.forEach( nodes, lang.hitch( this, function( node ) {
				// cut off domain name
				node.label = this._cutDomain( node.label );
				this.onChange( node );
			} ) );
		},

		onChange: function( item ) {
			// event stub
		}
	});
});
