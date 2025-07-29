/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
