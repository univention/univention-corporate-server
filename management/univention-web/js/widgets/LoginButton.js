/*
 * SPDX-FileCopyrightText: 2017-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"umc/widgets/Button",
	"login/main",
	"umc/i18n!"
], function(declare, lang, domClass, Button, login, _) {
	return declare("umc.widgets.LoginButton", [ Button ], {
		type: 'button',
		label: _('Login'),

		iconClass: 'lock',

		loggedIn: false,

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcLoginButton ucsTextButton');
		},

		_setLoggedInAttr: function(loggedIn) {
			this.set('iconClass', loggedIn ? 'unlock' : 'lock');
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


