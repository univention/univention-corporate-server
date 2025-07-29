/*
 * SPDX-FileCopyrightText: 2013-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,crypto*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/modules/udm/wizards/CreateWizard",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, tools, CreateWizard, _) {

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
			array.forEach(this.pages, function(page) {
				array.forEach(this.getPage(page.name)._form.widgets, function(widget) {
					var ucrkey = widget.id;
					if (widget.name === '_invite') {
						widget.id = '_invite';
						ucrkey = 'invite';
					}
					var wid = this.getWidget(page.name, widget.id);
					var visibility = this.ucr['directory/manager/web/modules/users/user/wizard/property/' + ucrkey + '/visible'];
					var defaultValue = this.ucr['directory/manager/web/modules/users/user/wizard/property/' + ucrkey + '/default'];
					if (visibility) {
						wid.set('visible', tools.isTrue(visibility));
					}
					if (defaultValue) {
						if (wid.declaredClass === "umc.widgets.CheckBox") {
							defaultValue = tools.isTrue(defaultValue || 'false');
						}
						// FIXME: the initial value setting does not trigger onChange(), therefore we must set "invite" here
						wid.set('value', defaultValue);
					}
				}, this);
			}, this);
		},

		postMixInProperties: function() {
			if (array.some(this.properties, function(prop) { return prop.id === 'mailPrimaryAddress' && prop.required; })) {
				this.widgetPages[0].widgets.push(['mailPrimaryAddress']);
			}
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
			} else if (widgetName === '_invite') {
				return {
					name: widgetName,
					size: 'Two',
					label: _('Invite user via e-mail. Password will be set by the user'),
					required: false,
					// FIXME: value: tools.isTrue(this.ucr['directory/manager/web/modules/users/user/wizard/property/invite/default'] || 'false'),
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

