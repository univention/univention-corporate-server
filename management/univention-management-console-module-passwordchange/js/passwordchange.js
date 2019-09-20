/*
 * Copyright 2014-2019 Univention GmbH
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
	"dojo/topic",
	"login",
	"umc/menu",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Text",
	"umc/widgets/PasswordBox",
	"umc/widgets/PasswordInputBox",
	"umc/i18n!umc/hooks/passwordchange"
], function(declare, lang, topic, login, menu, tools, dialog, Text, PasswordBox, PasswordInputBox, _) {

	var setPassword = function(values) {
		tools.umcpCommand('set', {
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
				content: _('Change the password of user "%s":', tools.status('username'))
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
