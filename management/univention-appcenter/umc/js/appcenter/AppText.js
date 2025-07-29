/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
], function(declare, _WidgetBase, _TemplatedMixin) {
	const AppText = declare("umc.modules.appcenter.AppText", [_WidgetBase, _TemplatedMixin], {
		baseClass: 'umcAppText',
		templateString: `
			<div>
				<div
					class="umcTile__box"
					style="background: \${app.bgc}"
				>
					<img
						class="umcTile__logo"
						src="\${app.logo}"
						alt="\${app.name} logo"
						onerror="this.src='/univention/management/modules/appcenter/icons/logo_fallback.svg'"
					>
				</div>
				<span class="umcTile__name">\${app.name}</span>
			</div>
		`
	});
	AppText.appFromApp = function(app) {
		return {
			bgc: app.backgroundColor || "",
			logo: "/univention/js/dijit/themes/umc/icons/scalable/" + app.logoName,
			name: app.name,
		};
	};
	return AppText;
});

