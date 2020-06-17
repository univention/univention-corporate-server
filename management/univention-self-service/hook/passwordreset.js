/*
 * Copyright 2015-2020 Univention GmbH
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
	'dojo/topic',
	'dojo/dom',
	'dojox/html/entities',
	'login',
	'login/dialog',
	'umc/menu',
	'umc/tools',
	'self-service',
	'self-service/PasswordForgotten',
	'self-service/ProtectAccountAccess',
	'umc/i18n!umc/hooks/passwordreset'
], function(topic, dom, entities, login, dialog, menu, tools, selfservice, PasswordForgotten, ProtectAccountAccess, _) {
	function isSelfServiceURL() {
		return window.location.pathname.indexOf('/univention/self-service/') === 0;
	}

	function gotoPage(subPage) {
		topic.publish('/umc/actions', 'menu', 'user-settings', subPage);
		if (isSelfServiceURL()) {
			window.location.hash = '#page=' + subPage;
			menu.close();
		} else {
			// open a new tab
			window.open('/univention/self-service/' + window.location.search + '#page=' + subPage);
		}
	}

	var enabledPages = selfservice.getEnabledPages();
	if (enabledPages.includes(ProtectAccountAccess)) {
		menu.addEntry({
			parentMenuId: 'umcMenuUserSettings',
			label: _('Protect your account'),
			priority: -10,
			onClick: function() {
				gotoPage(ProtectAccountAccess.hash);
			}
		});
	}
	if (enabledPages.includes(PasswordForgotten)) {
		var passwordResetEntry = menu.addEntry({
			parentMenuId: 'umcMenuUserSettings',
			priority: -5,
			label: _('Forgot your password?'),
			onClick: function() {
				gotoPage(PasswordForgotten.hash);
			}
		});
		login.onLogin(function() {
			// user has logged in -> hide menu entry
			menu.hideEntry(passwordResetEntry);
		});
		login.onLogout(function() {
			// user has logged out -> show menu entry
			menu.showEntry(passwordResetEntry);
		});
	}

	// add "Forgot password?" link to login page
	dialog.addLinkFromUcr('forgot_your_password', {
		text: _('Forgot your password?'),
		href: '/univention/self-service/#page=passwordreset'
	});
});

