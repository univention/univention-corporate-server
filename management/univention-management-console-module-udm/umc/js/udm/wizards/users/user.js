/*
 * Copyright 2013-2019 Univention GmbH
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
/*global define,crypto*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/modules/udm/wizards/CreateWizard",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, CreateWizard, _) {

	return declare("umc.modules.udm.wizards.users.user", [ CreateWizard ], {
		widgetPages: [
			{ // page one
				widgets: [
					['title', 'firstname', 'lastname'], // row one
					['username'] // row two
					// TODO: show mailPrimaryAddress if there is a mail domain
					// ['mailPrimaryAddress'] // row three
				]
			}, { // page two
				widgets: [
					'password',
					'pwdChangeNextLogin',
					'overridePWLength',
					'disabled'
				]
			}
		],

		startup: function() {
			this.inherited(arguments);
			var widget = this.getWidget('page1', 'PasswordRecoveryEmail');
			var node;
			if (widget) {
				node = widget.domNode.parentNode.parentNode.parentNode;
				node.classList.add('wizardInvitationBox');
			}

			widget = this.getWidget('page1', 'password');
			node = widget.domNode.parentNode.parentNode.parentNode;
			node.classList.add('wizardInvitationBox');
		},

		postMixInProperties: function() {
			if (array.some(this.properties, function(prop) { return prop.id === 'PasswordRecoveryEmail'; })) {
				this.widgetPages[1].widgets.splice(1, 0, 'PasswordRecoveryEmail');
				this.widgetPages[1].widgets.splice(2, 0, '_invite');
			}
			this.inherited(arguments);
		},

		buildWidget: function(widgetName, originalWidgetDefinition) {
			if (widgetName === 'disabled') {
				return {
					name: widgetName,
					size: 'Two',
					label: _('Account disabled'),
					required: false,
					type: 'CheckBox'
				};
			} else  if (widgetName === '_invite') {
				return {
					name: widgetName,
					size: 'Two',
					label: _('Invite user via e-mail. Password will be set by the user'),
					required: false,
					onChange: lang.hitch(this, function(value) {
						var pwdChange = this.getWidget('page1', 'pwdChangeNextLogin');
						pwdChange.set('value', value);
						pwdChange.set('disabled', value);
						var pwdCheck = this.getWidget('page1', 'overridePWLength');
						pwdCheck.set('value', value);
						pwdCheck.set('disabled', value);
						this.getWidget('page1', 'password').set('visible', !value);
						this.getWidget('page1', 'password').set('required', !value);
						this.getWidget('page1', 'PasswordRecoveryEmail').set('visible', value);
						this.getWidget('page1', 'PasswordRecoveryEmail').set('required', value);
					}),
					type: 'CheckBox'
				};
			} else {
				if (widgetName === 'PasswordRecoveryEmail') {
					originalWidgetDefinition.visible = false;
					originalWidgetDefinition.label = _('Mail address to which the invitation link is sent to');
				}
				return this.inherited(arguments);
			}
		},

		getValues: function() {
			var values = this.inherited(arguments);
			var invite = values._invite;
			delete values._invite;
			if (invite) {
				var randomNumbers = new Uint8Array((new Date()).getMilliseconds() % 20 + 20);
				if (window.crypto) {
					crypto.getRandomValues(randomNumbers);
				} else {
					randomNumbers = randomNumbers.map(function() { return Math.random() * 256; });
				}
				var password = "";
				randomNumbers.forEach(function(number) {
					password = password + String.fromCharCode(number % 74 + 48);
				});
				values.password = password;
				values.pwdChangeNextLogin = true;
				values.overridePWLength = true;
			}
			var disabled = values.disabled;
			delete values.disabled;
			if (disabled) {
				values.disabled = '1';
			}
			return values;
		}

	});
});

