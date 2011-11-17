/*
 * Copyright 2011 Univention GmbH
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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._quota.PageContainer");

dojo.require("umc.i18n");
dojo.require("umc.store");

dojo.require("umc.modules._quota.PartitionPage");
dojo.require("umc.modules._quota.DetailPage");

dojo.declare("umc.modules._quota.PageContainer", [ dijit.layout.StackContainer, umc.i18n.Mixin ], {

	moduleID: null,
	partitionDevice: null,
	_partitionPage: null,
	_detailPage: null,

	i18nClass: 'umc.modules.quota',

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
		this._partitionPage = new umc.modules._quota.PartitionPage({
			partitionDevice: this.partitionDevice,
			moduleStore: umc.store.getModuleStore('id', this.moduleID + '/users'),
			headerText: this._('Partition: %s', this.partitionDevice),
			helpText: this._('Set, unset and modify filesystem quota')
		});
		this.addChild(this._partitionPage);
		this.connect(this._partitionPage, 'onShowDetailPage', function(userQuota) {
			this._detailPage.init(userQuota);
			this.selectChild(this._detailPage);
		});
	},

	renderDetailPage: function() {
		this._detailPage = new umc.modules._quota.DetailPage({
			partitionDevice: this.partitionDevice,
			headerText: this._('Add quota setting for a user on partition'),
			helpText: this._('Add quota setting for a user on partition')
		});
		this.addChild(this._detailPage);
		this.connect(this._detailPage, 'onClosePage', function() {
			this.selectChild(this._partitionPage);
		});
		this.connect(this._detailPage, 'onSetQuota', function(values) {
			umc.tools.umcpCommand('quota/users/set', values).then(dojo.hitch(this, function(data) {
				if (data.result.success === true) {
					this.selectChild(this._partitionPage);
					this._partitionPage.filter();
				}
			}));
		});
	}
});
