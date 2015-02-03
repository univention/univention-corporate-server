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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/dialog",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, tools, dialog, _) {

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
			this.__workaround_uvmm_down = false;

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
			if (parentItem.type == 'root') {
				this.umcpCommand('uvmm/group/query', {}).then(lang.hitch(this, function(data) {
					var results = data.result instanceof Array ? data.result : [];
					//results.sort();
					onComplete(array.map(results, lang.hitch(this, function(groupname) {
						return {
							id: groupname,
							label: groupname == 'default' ? _('Physical servers') : (groupname == 'cloudconnections' ? _('Cloud connections') : groupname),
							type: 'group',
							icon: 'uvmm-group'
						};
					})));
					this.__workaround_uvmm_down = true;
				}), lang.hitch(this, function(error) {
					var err = tools.parseError(error);
					if (err.status == 503 && !this.__workaround_uvmm_down) {
						this.__workaround_uvmm_down = true;
						dialog.notify(_('The UVMM service is currently not available. Please trigger a search to refresh the view.'));
					}
				}));
			} else if (parentItem.type == 'group' && parentItem.id == 'default') {
				this.umcpCommand('uvmm/node/query', {
					nodePattern: ''
				}).then(lang.hitch(this, function(data) {
					var results = data.result instanceof Array ? data.result : [];
					results.sort(tools.cmpObjects('label'));
					onComplete(array.map(results, lang.hitch(this, function(node) {
						node.label = this._cutDomain( node.label );
						return node;
					})));
				}));
			} else if (parentItem.type == 'node') {
				onComplete([]);
			} else if (parentItem.type == 'group' && parentItem.id == 'cloudconnections') {
				this.umcpCommand('uvmm/cloud/query', {
					nodePattern: ''
				}).then(lang.hitch(this, function(data) {
					var results = data.result instanceof Array ? data.result : [];
					results.sort(tools.cmpObjects('label'));
					onComplete(array.map(results, lang.hitch(this, function(node) {
						node.label = this._cutDomain( node.label );
						return node;
					})));
				}));
			} else if (parentItem.type == 'cloud') {
				onComplete([]);
			}
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
