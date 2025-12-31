/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dijit/Editor",
	"umc/widgets/_FormWidgetMixin",
	"dompurify/purify",
	"dijit/_editor/plugins/ViewSource",
	"dijit/_editor/plugins/FullScreen",
	"dojox/editor/plugins/PrettyPrint"
], function(declare, Editor, _FormWidgetMixin, purify) {
	return declare("umc.widgets.Editor", [ Editor, _FormWidgetMixin ], {
		labelPosition: 'top',
		extraPlugins: ['viewSource', 'fullscreen', 'prettyprint'],

		postMixInProperties: function() {
			this.inherited(arguments);
			this.contentPreFilters.push(purify.sanitize);
			this.contentPostFilters.push(purify.sanitize);
		},

		ready: function() {
			return this.onLoadDeferred;
		}
	});
});

