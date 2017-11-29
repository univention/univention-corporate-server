/*
 * Copyright 2017 Univention GmbH
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
	"umc/dialog",
	"umc/widgets/Grid",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/Module",
	"umc/i18n!umc/modules/rejects"
], function(declare, lang, array, dialog, Grid, tools, Page, Module, _) {
	return declare("umc.modules.rejects", [Module], {
		idProperty: 'ucs_dn',
		_grid: null,
		postMixInProperties: function() {
			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._page = new Page({
				headerText: this.description,
				helpText: ''
			});

			this.addChild(this._page);

			var actions = [{
				name: 'delete',
				label: _('Delete'),
				description: _('Deleting the selected objects.'),
				isStandardAction: true,
				isMultiAction: true,
				iconClass: 'umcIconDelete',
				callback: lang.hitch(this, function(ids, items) {
					dialog.confirm(_('Are you sure to delete the %d selected connector reject(s)?', items.length), [{
						label: _('cancel'),
						'default': true
					}, {
						label: _('Delete'),
						callback: lang.hitch(this, function() {
							this.standbyDuring(tools.forEachAsync(items, function(item) {
								tools.umcpCommand('rejects/remove', item);
							}));
						})
					}]);
				})
			}];

			var columns = [{
				name: 'rejected',
				label: _('rejected by'),
				width: '10%'
			}, {
				name: 'ucs_dn',
				label: _('UCS DN'),
				width: '45%'
			}, {
				name: 's4_dn',
				label: _('S4 DN'),
				width: '45%'
			}];

			this._grid = new Grid({
				region: 'main',
				actions: actions,
				columns: columns,
				moduleStore: this.moduleStore,
				query: {rejected: '', ucs_dn: '', s4_dn: ''}
			});

			this._page.addChild(this._grid);
			this._page.startup();
		},
	});
});
