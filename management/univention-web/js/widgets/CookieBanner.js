/*
 * Copyright 2020-2022 Univention GmbH
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
	"dojo/cookie",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/ConfirmDialog",
	"umc/i18n/tools",
	"umc/i18n!"
], function(declare, cookie, tools, dialog, ConfirmDialog, i18nTools, _) {
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
			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);
			this.on('confirm', function(response) {
				this.close();
				if (response === 'accept') {
					var d = new Date();
					cookie(this.cookieName, d.toUTCString(), { path: '/', 'max-age': 60 * 60 * 24 * 365 });
				};
			});
		}
	});
});

