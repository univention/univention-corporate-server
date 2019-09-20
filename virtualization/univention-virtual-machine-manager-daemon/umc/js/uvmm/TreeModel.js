/*
 * Copyright 2011-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/dialog",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, tools, dialog, types, _) {

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
							label: this._getGroupNameLabel(groupname),
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
				this.getNodes('uvmm/node/query', onComplete);
			} else if (parentItem.type == 'node') {
				onComplete([]);
			} else if (parentItem.type == 'group' && parentItem.id == 'cloudconnections') {
				this.getNodes('uvmm/cloud/query', onComplete);
			} else if (parentItem.type == 'cloud') {
				onComplete([]);
			}
		},

		_getGroupNameLabel: function(groupname) {
			var label;
			switch (groupname) {
				case 'default':
					label = _('Physical servers');
					break;
				case 'cloudconnections':
					label = _('Cloud connections');
					break;
				default:
					label = groupname;
			}
			label = lang.replace(
				'<span class="tree-description" title="{label}">{label}</span>',
				{label: label}
			);
			if (groupname === 'default') {
				label += '<span class="node-ressources">CPU | Mem<span>';
			}
			return label;
		},

		getNodes: function(command, onComplete) {
			this.umcpCommand(command, {
				nodePattern: ''
			}).then(lang.hitch(this, function(data) {
				var results = data.result instanceof Array ? data.result : [];
				results.sort(tools.cmpObjects('label'));
				onComplete(array.map(results, lang.hitch(this, function(node) {
					if (this._nodeHasRessources(node)) {
						node.label = this._getRessourceNodeLabel(node);
					} else {
						node.label = lang.replace(
							'<span class="tree-description" title="{label}">{label}</span>',
							{label: this._cutDomain(node.label)}
						);
					}
					return node;
				})));
			}));
		},

		_nodeHasRessources: function(node) {
			var hasRessources = array.every(['cpuUsage', 'memUsed', 'memPhysical'], function(resource) {
				return node.hasOwnProperty(resource);
			});
			return hasRessources && node.memPhysical !== 0 && node.available;
		},

		_getRessourceNodeLabel: function(node) {
			var shortName = this._cutDomain(node.label);
			var label = lang.replace(
				'<span title="{shortName}" class="tree-description">{shortName}</span>' +
				'<span title="CPU usage: {cpu}%; Memory usage: {memUsed}/{memPhysical}" ' +
				'class="node-ressources">{cpu}% | {mem}%</span>',
				{
					cpu: this._formatPercent(node.cpuUsage * 100),
					mem: this._formatPercent(node.memUsed / node.memPhysical * 100),
					shortName: shortName,
					memPhysical: types.prettyCapacity(node.memPhysical),
					memUsed: types.prettyCapacity(node.memUsed)
				}
			);
			return label;
		},

		_formatPercent: function(number) {
			number = parseInt(number);
			if (number < 10) {
				return '\u2007' + '\u2007' + number;
			} else if (number < 100) {
				return '\u2007' + number;
			}
			return number;
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
