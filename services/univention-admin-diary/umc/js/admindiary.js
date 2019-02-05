/*
 * Copyright 2011-2019 Univention GmbH
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
	"umc/tools",
	"umc/widgets/Module",
	"umc/modules/admindiary/OverviewPage",
	"umc/modules/admindiary/DetailsPage",
	"umc/i18n!umc/modules/admindiary"
], function(declare, lang, array, dialog, tools, Module, OverviewPage, DetailsPage, _) {
	return declare("umc.modules.admindiary", [ Module ], {
		moduleStore: null,
		idProperty: 'context_id',

		buildRendering: function() {
			this.inherited(arguments);

			this.standbyDuring(tools.umcpCommand('admindiary/options').then(lang.hitch(this, function(data) {
				this._overviewPage = new OverviewPage({
					moduleStore: this.moduleStore,
					tags: data.result.tags,
					authors: data.result.usernames,
					sources: data.result.hostnames,
					events: data.result.events,
				});
				this.addChild(this._overviewPage);
				this._detailsPage = new DetailsPage({
				});
				this.addChild(this._detailsPage);
				this._overviewPage.on('ShowDetails', lang.hitch(this, '_showDetails'));
				this._detailsPage.on('Close', lang.hitch(this, '_closeDetails'));
				this.selectChild(this._overviewPage);
			})));
		},

		_closeDetails: function() {
			this.selectChild(this._overviewPage);
		},

		_showDetails: function(context_id) {
			this.standbyDuring(tools.umcpCommand('admindiary/get', {'context_id': context_id}).then(lang.hitch(this, function(data) {
				this._detailsPage.reset(data.result);
				this.selectChild(this._detailsPage);
			})));
		}
	});
});
