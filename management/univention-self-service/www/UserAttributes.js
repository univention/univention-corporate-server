/*
 * Copyright 2019 Univention GmbH
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
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/keys",
	"dojo/Deferred",
	"dojo/promise/all",
	"dojo/on",
	"dojox/html/entities",
	"login",
	"umc/render",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Form",
	"umc/widgets/Button",
	"./TextBox",
	"./PasswordBox",
	"put-selector/put",
	"umc/i18n!."
], function(lang, array, keys, Deferred, all, on, entities, login, render, tools, dialog, Form, Button, TextBox, PasswordBox, put, _) {

	return {
		title: _('Your profile'),
		desc: _('Customize your profile'),
		hash: 'profiledata',
		contentContainer: null,
		steps: null,
		standby: null,

		startup: function() {
			if (this._username.value !== '') {
				this._password.focus();
			} else {
				this._username.focus();
			}
		},

		getDesc: function() {
			return _(this.desc);
		},

		getTitle: function() {
			return _(this.title);
		},

		getContent: function() {
			if (!this.contentContainer) {
				this.contentContainer = put('div.contentWrapper');
				put(this.contentContainer, 'h2', this.getTitle());
				put(this.contentContainer, 'div.contentDesc', this.getDesc());
				put(this.contentContainer, this._getSteps());
			}
			return this.contentContainer;
		},

		/**
		 * Return the steps for the content node.
		 * If the steps do not exists, they will be generated.
		 * Note: Please call getContent for generating the steps.
		 * */
		_getSteps: function() {
			if (!this.steps) {
				this.steps = put('ol.PasswordOl');
				this._createUsername();
				this._createPassword();
				this._createSubmit();
			}
			return this.steps;
		},

		/**
		 * Creates input field for username.
		 * */
		_createUsername: function() {
			this._username = new TextBox({
				'class': 'soloLabelPane',
				isValid: function() {
					return !!this.get('value');
				},
				required: true
			});
			this._username.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._getUserAttributes();
				}
			}));

			put(this.steps, 'li.step div.stepLabel $ <', _('Username'), this._username.domNode);

			this._username.startup();
			login.onInitialLogin(lang.hitch(this, function(username) {
				this._username.set('value', tools.status('username'));
				this._username.set('disabled', true);
			}));
		},

		/**
		 * Creates input field for password.
		 * */
		_createPassword: function() {
			this._password = new PasswordBox({
				'class': 'soloLabelPane',
				required: true,
			});
			this._password.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._getUserAttributes();
				}
			}));

			put(this.steps, 'li.step div.stepLabel $ <', _('Password'), this._password.domNode);

			this._password.startup();
		},

		/**
		 * Creates submit button.
		 * */
		_createSubmit: function() {
			this._getUserAttributesButton = new Button({
				label: _('Next'),
				callback: lang.hitch(this, '_getUserAttributes')
			});
			put(this.steps, 'div.buttonRow.umcPageFooter', this._getUserAttributesButton.domNode);
		},

		/**
		 *
		 * */
		_getUserAttributes: function() {
			var validCredentials = this._username.isValid() && this._password.isValid();
			if (validCredentials) {
				this.standby.show();
				var data = {
					'username': this._username.get('value'),
					'password': this._password.get('value')
				};
				tools.umcpCommand('passwordreset/get_user_attributes', data)
					.then(lang.hitch(this, function(data) {
						this._username.set('disabled', true);
						this._password.set('disabled', true);
						this._getUserAttributesButton.hide();
						this._createUserAttributesStep(data.result);
					}))
					.otherwise(lang.hitch(this, function(data) {
						this._username.reset();
						this._password.reset();
						this.standby.hide();
					}));
			} else {
				if (!this._username.isValid()) {
					this._username.focusInvalid();
				} else if (!this._password.isValid()) {
					this._password.focusInvalid();
				}
			}
		},

		_createUserAttributesStep: function(data) {
			if (!data.widget_descriptions.length) {
				dialog.alert(_('There is no profile data data defined that you can edit'));
			}
			this._userAttributesStep = put(this.steps, 'li.step div.stepLabel', _('Customize your profile'), '<');

			var widgetDescriptions = this._prepareWidgets(data.widget_descriptions);
			render.requireWidgets(widgetDescriptions)
				.then(lang.hitch(this, function() {
					this._form = new Form({
						widgets: widgetDescriptions,
						layout: data.layout,
						onSubmit: lang.hitch(this, '_setUserAttributes')
					});

					this._saveButton = new Button({
						label: _('Save'),
						callback: lang.hitch(this._form, 'onSubmit')
					});

					this._cancelButton = new Button({
						label: _('Cancel'),
						callback: lang.hitch(this, '_deleteUserAttributesStep')
					});

					put(this._userAttributesStep, this._form.domNode);
					put(this._userAttributesStep, 'div.buttonRow.umcPageFooter', this._cancelButton.domNode, '<', this._saveButton.domNode);

					on(this._form, 'valuesInitialized', lang.hitch(this, function() {
						this._form.setFormValues(data.values);
						this._form.ready()
							.then(lang.hitch(this, function() {
								this._initialFormValues = this._form.get('value');
								this.standby.hide();
							}));
					}));
					this._form.startup();
				}));
		},

		// TODO
		// this is duplicated in udm/DetailPage.js
		//
		// move this into management/univention-management-console-module-udm/umc/python/udm/syntax.py ?
		// or render.js ?
		_prepareWidgets: function(props) {
			array.forEach(props, function(iprop) {
				iprop.disabled = iprop.readonly || !iprop.editable;
				iprop.size = 'Two';
			});

			return props;
		},

		_setUserAttributes: function() {
			this._form.setValid(null);

			// frontend validation (like valid choice in ComboBox)
			if (!this._form.validate()) {
				this._form.focusFirstInvalidWidget();
				return;
			}

			var alteredValues = tools.objFilter(this._form.get('value'), lang.hitch(this, function(key, value) {
				return !tools.isEqual(value, this._initialFormValues[key]);
			}));

			if (!Object.keys(alteredValues).length) {
				dialog.contextNotify(_('Your profile data is up to date'));
				return;
			}

			// backend validation
			this.standby.show();
			var data = {
				username: this._username.get('value'),
				password: this._password.get('value'),
				attributes: alteredValues
			};
			tools.umcpCommand('passwordreset/validate_user_attributes', data)
				.then(lang.hitch(this, function(data) {
					var isValid = function(v) {
						return Array.isArray(v.isValid) ? v.isValid.every(function(_isValid) { return _isValid; }) : v.isValid;
					};

					var allValid = tools.values(data.result).every(function(v) {
						return isValid(v);
					});

					var validDeferred = new Deferred();
					if (allValid) {
						validDeferred.resolve();
					} else {
						this._form.setValid(tools.objFilter(data.result, function(k, v) {
							return !isValid(v);
						}));
						this._form.focusFirstInvalidWidget();
						validDeferred.reject();
					}

					return validDeferred;
				}))
				.then(lang.hitch(this, function() {
					tools.umcpCommand('passwordreset/set_user_attributes', data)
						.then(lang.hitch(this, function(data) {
							dialog.contextNotify(entities.encode(data.result));
							this._initialFormValues = this._form.get('value');
						}))
						.always(lang.hitch(this.standby, 'hide'));
				}))
				.otherwise(lang.hitch(this.standby, 'hide'));
		},

		_deleteUserAttributesStep: function() {
			put(this._userAttributesStep, '!');
			this._form.destroyRecursive();

			this._username.reset();
			this._password.reset();
			this._getUserAttributesButton.show();
		}
	};
});
