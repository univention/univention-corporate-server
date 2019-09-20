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
	"dijit/form/Button",
	"login/main",
	"umc/i18n!"
], function(declare, lang, domClass, Button, login, _) {
	return declare("umc.widgets.Button", [ Button ], {
		type: 'button',
		label: _('Login'),

		'class': 'umcLoginButton umcFlatButton',

		loggedIn: false,

		buildRendering: function() {
			this.inherited(arguments);
			this.set('iconClass', 'umcLoggedOutIcon');
		},

		_setLoggedInAttr: function(loggedIn) {
			this.set('iconClass', loggedIn ? 'umcLoggedInIcon' : 'umcLoggedOutIcon');
			this.set('label', loggedIn ? _('Logout') : _('Login'));
			this._set('loggedIn', loggedIn);
		},

		emphasise: function(bool) {
			domClass.toggle(this.domNode, 'umcLoginButton--emphasised', bool);
		},

		postCreate: function() {
			this.inherited(arguments);

			login.onLogin(lang.hitch(this, 'set', 'loggedIn', true));
			login.onLogout(lang.hitch(this, 'set', 'loggedIn', false));

			this.on('click', lang.hitch(this, function() {
				if (this.loggedIn) {
					login.logout();
				} else {
					login.start();
				}
			}));
		}
	});
});


