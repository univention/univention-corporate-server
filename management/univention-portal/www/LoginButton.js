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
	"dojo/dom-class",
	"umc/widgets/Button",
	"login/main",
	"portal",
	"umc/i18n!"
], function(declare, domClass, Button, login, portal, _) {
	return declare("portal.LoginButton", [ Button ], {
		iconClass: 'portalLoggedOutIcon',

		description: _('Login'),

		postMixInProperties: function() {
			this.inherited(arguments);
			this.callback = function() {
				login.start(null, null, true, function(saml) {
					portal.showLoginInIFrame(saml);
				});
			};
		},

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'portalLoginButton portalSidebarButton umcFlatButton');
		},

		postCreate: function() {
			this.inherited(arguments);
			if (this._tooltip) {
				this._tooltip.position = ['after-centered'];
				this._tooltip.showDelay = 0;
				this._tooltip.hideDelay = 0;
			}
		},

		emphasise: function(bool) {
			domClass.toggle(this.domNode, 'umcLoginButton--emphasised', bool);
		}
	});
});



