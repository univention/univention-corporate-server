/*
 * SPDX-FileCopyrightText: 2020-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/array",
	"dojo/cookie",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/ConfirmDialog",
	"umc/i18n/tools",
	"umc/i18n!"
], function(declare, array, cookie, tools, dialog, ConfirmDialog, i18nTools, _) {
	return declare("umc.widgets.CookieBanner", [ ConfirmDialog ], {
		// summary:
		//		Display cookie banner
		// usage:
		//		(new CookieBanner()).show();
		'class': 'umcCookieBanner',
		closable: false,
		draggable: false,

		postMixInProperties: function() {
			this.inherited(arguments);
			var banner = tools.status('cookieBanner');
			this.cookieName = banner['cookie'] || 'univentionCookieSettingsAccepted';
			var locale = i18nTools.defaultLang().slice(0, 2);
			this.title = banner['title'][locale] || _('Cookie Settings');
			this.message = banner['text'][locale] || _('We use cookies in order to provide you with certain functions and to be able to guarantee an unrestricted service. By clicking on "Accept", you consent to the collection of information on this portal.');
			this.options = [{
				name: 'accept',
				label: _('Accept'),
				'default': true
			}];
		},

		show: function() {
			if (!tools.status('cookieBanner')['show']) {
				return;
			}
			if (cookie(this.cookieName)) {
				return;
			}
			var banner = tools.status('cookieBanner');
			if (banner['domains'].length > 0) {
				if (! array.some(banner['domains'], function(dom) { return document.domain.endsWith(dom); })) {
					return;
				};
			}
			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);
			this.on('confirm', function(response) {
				this.close();
				var banner = tools.status('cookieBanner');
				var domain = document.domain;
				array.some(banner['domains'], function(dom) {
					if (document.domain.endsWith(dom)) {
						domain = dom;
						return true;
					}
					return false;
				});
				if (response === 'accept') {
					var d = new Date();
					cookie(this.cookieName, d.toUTCString(), { domain: domain, path: '/', 'max-age': 60 * 60 * 24 * 365 });
				};
			});
		}
	});
});

