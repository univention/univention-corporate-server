/*
 * SPDX-FileCopyrightText: 2014-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/topic",
	"dojox/html/entities",
	"login",
	"umc/menu",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Text",
	"umc/widgets/PasswordBox",
	"umc/widgets/PasswordInputBox",
	"umc/i18n!umc/hooks/passwordchange"
], function(declare, lang, topic, entities, login, menu, tools, dialog, Text, PasswordBox, PasswordInputBox, _) {

	var setPassword = function(values) {
		tools.umcpCommand('set/password', {
			password: values
		}, false).then(lang.hitch(this, function() {
			dialog.alert(_('The password has been changed successfully.'));
		}), lang.hitch(this, function(err) {
			err = tools.parseError(err);
			dialog.confirm(err.message, [{
				label: _('OK'),
				'default': true
			}], _('Error changing password')).then(showPasswordChangeDialog);
		}));
	};

	var showPasswordChangeDialog = function() {
		menu.close();
		dialog.confirmForm({
			widgets: [{
				type: Text,
				name: 'text',
				content: _('Change the password of user "%s":', entities.encode(tools.status('username')))
			}, {
				name: 'password',
				type: PasswordBox,
				label: _('Old password')
			}, {
				name: 'new_password',
				type: PasswordInputBox,
				twoRows: true,
				label: _('New password')
			}],
			title: _('Change password'),
			submit: _('Change password'),
		}).then(setPassword, function() {});
	};

	topic.publish('/portal/menu', 'userMenu', 'addItem', {
		$priority: 0,
		label: _('Change password'),
		onClick: function() {
			topic.publish('/umc/actions', 'menu', 'passwordchange');
			showPasswordChangeDialog();
		}
	});
	var entry = menu.addEntry({
		id: 'umcMenuChangePassword',
		parentMenuId: 'umcMenuUserSettings',
		label: _('Change password'),
		onClick: function() {
			topic.publish('/umc/actions', 'menu', 'passwordchange');
			showPasswordChangeDialog();
		}
	});
	menu.hideEntry(entry);

	login.onLogin(function() {
		// user has logged in -> show menu entry
		menu.showEntry(entry);
	});

	login.onLogout(function() {
		// user has logged out -> hide menu entry
		menu.hideEntry(entry);
	});
});
