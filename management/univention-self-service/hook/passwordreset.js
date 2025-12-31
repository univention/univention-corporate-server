/*
 * SPDX-FileCopyrightText: 2015-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
	'umc/i18n!umc/hooks/passwordreset'
], function(topic, dom, entities, login, dialog, menu, tools, _) {
	function gotoPage(subPage) {
		topic.publish('/umc/actions', 'menu', 'user-settings', subPage);
		// open a new tab
		window.open('/univention/selfservice/#/selfservice/' + subPage);
	}

	if (tools.isTrue(tools.status('umc/self-service/protect-account/frontend/enabled'))) {
		menu.addEntry({
			parentMenuId: 'umcMenuUserSettings',
			label: _('Protect your account'),
			priority: -10,
			onClick: function() {
				gotoPage('protectaccount');
			}
		});
	}

	if (tools.isTrue(tools.status('umc/self-service/passwordreset/frontend/enabled'))) {
		var passwordResetEntry = menu.addEntry({
			parentMenuId: 'umcMenuUserSettings',
			priority: -5,
			label: _('Forgot your password?'),
			onClick: function() {
				gotoPage('passwordforgotten');
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
		href: '/univention/selfservice/#/selfservice/passwordforgotten'
	});
});

