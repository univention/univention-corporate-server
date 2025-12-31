/*
 * SPDX-FileCopyrightText: 2020-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojox/html/entities",
	"umc/widgets/Text",
	"./AppText",
	"umc/i18n!umc/modules/appcenter"
], function(declare, entities, Text, AppText, _) {
	return {
		getPageConf: function(app) {
			if (!app.licenseAgreement) {
				return null;
			}

			return {
				name: `licenseAgreement_${app.id}`,
				headerText: '',
				helpText: _('License agreements'),
				widgets: [{
					type: AppText,
					app: AppText.appFromApp(app),
					name: 'appText'
				}, {
					type: Text,
					'class': 'appInstallDialog__readme',
					name: `licenseAgreement_licenseAgreement_${app.id}`,
					content: entities.encode(app.licenseAgreement)
				}]
			};
		}
	};
});

