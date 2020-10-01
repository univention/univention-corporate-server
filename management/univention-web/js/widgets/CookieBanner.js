/*
 * Copyright 2020 Univention GmbH
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
	"umc/i18n!"
], function(declare, cookie, tools, dialog, ConfirmDialog, _) {
	return declare("umc.widgets.CookieBanner", [ ConfirmDialog ], {
		// summary:
		//		Display cookie banner
		'class': 'umcCookieBanner',
		closable: false,

		postMixInProperties: function(props) {
			this.inherited(arguments);
			this.title = _('Cookie settings');
			this.message = tools.status('cookieMessage');
			this.options = [{
				name: 'accept',
				label: _('Accept'),
				'default': true
			}];
		},


		show: function() {
			if (!cookie('univentionCookieSettingsAccepted')) {
				this.inherited(arguments);
			}
		},

		buildRendering: function() {
			this.inherited(arguments);
			this.on('confirm', function(response) {
				this.close();
				if (response === 'accept') {
					cookie('univentionCookieSettingsAccepted', 'true');
				};
			});
			this.set('title', _('Cookie settings'));
			this.set('message', tools.status('cookieMessage'));
		}
	});
});

