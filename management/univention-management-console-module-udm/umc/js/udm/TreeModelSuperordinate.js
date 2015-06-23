/*
 * Copyright 2013-2015 Univention GmbH
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
/*global define console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/modules/udm/TreeModel",
	"umc/modules/udm/cache"
], function(declare, lang, array, tools, TreeModel, cache) {
	return declare('umc.modules.udm.TreeModelSuperordinate', [TreeModel], {

		rootName: null,
		moduleFlavor: null,

		getRoot: function(onItem) {
			this.root = {
				objectType: this.moduleFlavor,
				icon: "udm-" + this.moduleFlavor.replace('/', '-'),
				id: "None",
				label: this.rootName,
				root: true,
				operations: []
			};
			onItem(this.root);
		},

		mayHaveChildren: function(item) {
			return item.root;
		},

		getChildren: function(parentItem, onComplete) {
			cache.get(this.moduleFlavor).getSuperordinates(undefined, true).then(lang.hitch(this, function(data) {
				// sort items alphabetically
				var superordinates = data instanceof Array ? lang.clone(data) : [];
				superordinates.sort(tools.cmpObjects('label'));
				// remove None superordinate
				superordinates = array.filter(superordinates, function(item) { return item.id !== 'None'; });

				try {
					onComplete(superordinates);
				} catch (error) {
					// don't do anything
				}
			}), lang.hitch(this, function() {
				try {
					onComplete([]);
				} catch (error) {
					// don't do anything
				}
			}));
		}
	});
});
