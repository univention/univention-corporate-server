/*
 * SPDX-FileCopyrightText: 2020-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"./AppSettings",
	"./AppSettingsForm",
	"./AppText",
	"umc/i18n!umc/modules/appcenter"
], function(declare, AppSettings, AppSettingsForm, AppText, _) {
	return {
		getPageConf: function(app, appSettings) {
			const formConf = AppSettings.getFormConf(app, appSettings.values, 'Install');
			if (!formConf) {
				return null;
			}

			const appSettingsFormName = `appSettings_appSettings_${app.id}`;
			return {
				name: `appSettings_${app.id}`,
				$appSettingsFormName: appSettingsFormName,
				headerText: '',
				helpText: _('App settings'),
				widgets: [{
					type: AppText,
					app: AppText.appFromApp(app),
					name: 'appText'
				}, {
					type: AppSettingsForm,
					name: appSettingsFormName,
					size: 'Two',
					widgets: formConf.widgets,
					layout: formConf.layout
				}]
			};
		}
	};
});






