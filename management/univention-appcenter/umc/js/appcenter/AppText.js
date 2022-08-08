/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2021-2022 Univention GmbH
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

