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
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojo/Deferred",
	"umc/tools",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"login/main",
	"./_Menu",
	"umc/i18n!"
], function(declare, lang, domClass, Deferred, tools, ContainerWidget, Text, login, PortalMenu, _) {

	var userMenuDeferred = new Deferred();

	var UserMenu = declare('portal.UserMenu', [PortalMenu], {
		postMixInProperties: function() {
			this.inherited(arguments);
			this.$wrapper = new ContainerWidget({});
			this._userNameText = new Text({
				'class': 'dijitDisplayNone portalUserMenu__userName',
				content: ''
			});
			this.$wrapper.addChild(this._userNameText);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this.addItem({
				$priority: 50,
				label: _('Logout'),
				iconClass: 'dijitNoIcon',
				onClick: function() {
					login.logout();
				}
			});
		},

		postCreate: function() {
			this.inherited(arguments);
			if (userMenuDeferred.isResolved()) {
				console.warn('UserMenu created twice: only the first created UserMenu gets the subsequently added menu entries (like from univention-self-service/hook/passwordreset.js). The UserMenu was not intended to exist more than once');
			} else {
				userMenuDeferred.resolve(this);
			}

			login.onLogin(lang.hitch(this, function() {
				var userName = tools.status('username');
				if (userName) {
					this._userNameText.set('content', userName);
					domClass.remove(this._userNameText.domNode, 'dijitDisplayNone');
				}
			}));
			login.onLogout(lang.hitch(this, function() {
				this._userNameText.set('content', '');
				domClass.add(this._userNameText.domNode, 'dijitDisplayNone');
			}));
		}
	});

	UserMenu.addItem = function(conf) {
		userMenuDeferred.then(function(userMenu) {
			userMenu.addItem(conf);
		});
	};

	return UserMenu;
});

