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
	"dijit/layout/StackContainer",
	"umc/tools",
	"umc/store",
	"umc/modules/quota/PartitionPage",
	"umc/modules/quota/DetailPage",
	"umc/i18n!umc/modules/quota"
], function(declare, lang, StackContainer, tools, store, PartitionPage, DetailPage, _) {
	return declare("umc.modules.quota.PageContainer", [ StackContainer ], {

		moduleID: null,
		partitionDevice: null,
		_partitionPage: null,
		_detailPage: null,

		buildRendering: function(partitionDevice) {
			this.inherited(arguments);
			this.renderPartitionPage();
			this.renderDetailPage();
		},

		postCreate: function() {
			this.inherited(arguments);
			this.selectChild(this._pageContainer);
		},

		renderPartitionPage: function() {
			this._partitionPage = new PartitionPage({
				partitionDevice: this.partitionDevice,
				moduleStore: store('id', this.moduleID + '/users'),
				headerText: _('Partition: %s', this.partitionDevice),
				helpText: _('Set, unset and modify filesystem quota')
			});
			this.addChild(this._partitionPage);
			this._partitionPage.on('ShowDetailPage', lang.hitch(this, function(userQuota) {
				this._detailPage.init(userQuota);
				this.selectChild(this._detailPage);
			}));
		},

		renderDetailPage: function() {
			this._detailPage = new DetailPage({
				partitionDevice: this.partitionDevice,
				headerText: _('Add quota setting for a user on partition'),
				helpText: _('Add quota setting for a user on partition')
			});
			this.addChild(this._detailPage);
			this._detailPage.on('ClosePage', lang.hitch(this, function() {
				this.selectChild(this._partitionPage);
			}));
			this._detailPage.on('SetQuota', lang.hitch(this, function(values) {
				tools.umcpCommand('quota/users/set', values).then(lang.hitch(this, function(data) {
					if (data.result.success === true) {
						this.selectChild(this._partitionPage);
						this._partitionPage.filter();
					}
				}));
			}));
		}
	});
});
