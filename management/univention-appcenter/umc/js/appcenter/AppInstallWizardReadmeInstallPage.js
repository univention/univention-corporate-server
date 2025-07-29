/*
 * SPDX-FileCopyrightText: 2020-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dompurify/purify",
	"umc/widgets/Text",
	"./AppText",
	"umc/i18n!umc/modules/appcenter"
], function(declare, purify, Text, AppText, _) {
	return {
		getPageConf: function(app, readme) {
			if (!app[readme]) {
				return null;
			}

			return {
				name: `readme_${app.id}`,
				headerText: '',
				helpText: _('Information'),
				widgets: [{
					type: AppText,
					app: AppText.appFromApp(app),
					name: 'appText'
				}, {
					type: Text,
					'class': 'appInstallDialog__readme',
					name: `readmeInstall_readme_${app.id}`,
					content: purify.sanitize(app[readme])
				}]
			};
		}
	};
});
