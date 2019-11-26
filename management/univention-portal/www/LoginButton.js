/*
 * Copyright 2017-2019 Univention GmbH
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
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/form/DropDownButton",
	"umc/widgets/Button",
	"umc/widgets/ContainerWidget",
	"login/main",
	"umc/i18n!"
], function(declare, lang, domClass, Menu, MenuItem, DropDownButton, Button, ContainerWidget, login, _) {
	return declare("portal.LoginButton", [ ContainerWidget ], {
		loggedIn: false,

		buildRendering: function() {
			this.inherited(arguments);

			this._loginButton = new Button({
				'class': 'portalLoginButton umcFlatButton',
				iconClass: 'portalLoggedOutIcon',
				description: _('Login'),
				callback: function() {
					login.start();
				}
			});
			this._loginButton._tooltip.position = ['after-centered']; // not handled by umc/widgets/Button

			var dropDown = new ContainerWidget({
				baseClass: 'portalAvatarMenuContainer',
				'class': 'foobar'
			});
			var menu = new Menu({
				'class': 'foobar_menu'
			});
			var logout = new MenuItem({
				label: _('Logout'),
				onClick: function() {
					login.logout();
				}
			});
			menu.addChild(logout);
			dropDown.addChild(menu);

			this._avatarButton = new DropDownButton({
				'class': 'portalLoginButton umcFlatButton dijitDisplayNone',
				iconClass: 'portalLoggedInIcon',
				dropDown: dropDown,
				dropDownPosition: ['after']
			});

			this.addChild(this._loginButton);
			this.addChild(this._avatarButton);

			window.t = this;
		},

		_setLoggedInAttr: function(loggedIn) {
			domClass.toggle(this._loginButton.domNode, 'dijitDisplayNone', loggedIn);
			domClass.toggle(this._avatarButton.domNode, 'dijitDisplayNone', !loggedIn);
			this._set('loggedIn', loggedIn);
		},

		emphasise: function(bool) {
			domClass.toggle(this._loginButton.domNode, 'umcLoginButton--emphasised', bool);
		},

		postCreate: function() {
			this.inherited(arguments);

			login.onLogin(lang.hitch(this, 'set', 'loggedIn', true));
			login.onLogout(lang.hitch(this, 'set', 'loggedIn', false));
		}
	});
});


