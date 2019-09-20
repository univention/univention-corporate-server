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
	"dojox/html/entities",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Module",
	"umc/modules/admindiary/OverviewPage",
	"umc/modules/admindiary/DetailsPage",
	"umc/i18n!umc/modules/admindiary",
	"xstyle/css!umc/modules/admindiary.css"
], function(declare, lang, array, entities, dialog, tools, Module, OverviewPage, DetailsPage, _) {
	return declare("umc.modules.admindiary", [ Module ], {
		moduleStore: null,
		idProperty: 'context_id',


		postMixInProperties: function() {
			this.inherited(arguments);
			this.selectablePagesToLayoutMapping = {
				'_overviewPage': 'searchpage-grid',
				'_detailsPage': ''
			};
		},

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
				this._detailsPage.on('Reload', lang.hitch(this, '_showDetails'));
				this._detailsPage.on('NewComment', lang.hitch(this, '_newComment'));
				var requestedContextId = this.get('moduleState');
				if (requestedContextId) {
					this._showDetails(requestedContextId);
				} else {
					this._closeDetails();
				}
			})));
		},

		_closeDetails: function() {
			this._set('moduleState', '');
			this.set('title', _('Admin Diary'));
			this.selectChild(this._overviewPage);
		},

		_newComment: function(values) {
			this.standbyDuring(tools.umcpCommand('admindiary/add_comment', values).then(lang.hitch(this, function(data) {
				this._showDetails(values.context_id);
			})));
		},

		_setModuleStateAttr: function(_state) {
			var currentState = this.get('moduleState');
			if (currentState === _state) {
				return;
			}
			this._set('moduleState', _state);
			this._showDetails(_state);
		},

		_showDetails: function(context_id) {
			this._set('moduleState', context_id);
			this.standbyDuring(tools.umcpCommand('admindiary/get', {'context_id': context_id}).then(lang.hitch(this, function(data) {
				this.set('title', lang.replace(_('Admin Diary: {event_name}'), {event_name: entities.encode(data.result[0].event)}));
				this._detailsPage.reset(context_id, data.result);
				this.selectChild(this._detailsPage);
			})));
		}
	});
});
