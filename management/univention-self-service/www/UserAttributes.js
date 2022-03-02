/*
 * Copyright 2019-2022 Univention GmbH
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
	"dojo/dom-class",
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
	"umc/i18n/tools",
	"umc/i18n!."
], function(lang, array, keys, Deferred, all, on, domClass, entities, login, render, tools, dialog, Form, Button, TextBox, PasswordBox, put, i18nTools, _) {

	return {
		hash: 'profiledata',
		enabledViaUcr: 'umc/self-service/profiledata/enabled',
		visible: true,
		allowAuthenticated: function() {
			return tools.isTrue(tools.status('umc/self-service/allow-authenticated-use'));
		},

		title: _('Your profile'),
		desc: _('Customize your profile'),
		contentContainer: null,
		steps: null,
		_autoLoaded: false,

		startup: function() {
			login.onInitialLogin(lang.hitch(this, function(username) {
				if (this._autoLoaded) {
					return;
				}
				this._autoLoaded = true;
				this._forceLoginChange = true;
				this._username.set('value', tools.status('username'));
				this._username.set('disabled', true);
				if (this.allowAuthenticated()) {
					this._password.set('disabled', true);
					domClass.toggle(this._passwordStep, 'dijitDisplayNone', true);
					this._getUserAttributes(true);
				}
			}));
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
			var locale = i18nTools.defaultLang().slice(0, 2);
			var ucrTitleKey = "umc/self-service/" + this.hash + "/title/" + locale;
			var ucrTitleKeyEnglish = "umc/self-service/" + this.hash + "/title/en";
			return tools.status(ucrTitleKey) || tools.status(ucrTitleKeyEnglish) || this.title;
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

			this._passwordStep = put(this.steps, 'li.step div.stepLabel.stepLabelProfilePassword $ <', _('Password'), this._password.domNode);

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
			put(this.steps, 'div.umcPageFooter div.umcPageFooterRight', this._getUserAttributesButton.domNode);
		},

		/**
		 *
		 * */
		_getUserAttributes: function() {
			var validCredentials = this._username.isValid() && this._password.isValid();
			if (validCredentials || this._forceLoginChange) {
				this.standby(true);
				tools.umcpCommand('passwordreset/get_user_attributes_descriptions', this.getCredentials())
					.then(lang.hitch(this, function(data) {
						var layout = array.map(data.result, function(item) { return item.id; });
						return tools.umcpCommand('passwordreset/get_user_attributes_values', lang.mixin(this.getCredentials(), {attributes: layout})).then(lang.hitch(this, function(data2) {
							this._username.set('disabled', true);
							this._password.set('disabled', true);
							this._getUserAttributesButton.hide();
							this._createUserAttributesStep({ widget_descriptions: data.result, layout: layout, values: data2.result });
						}));
					}))
					.otherwise(lang.hitch(this, function() {
						this._username.reset();
						this._password.reset();
						this.standby(false);
					}));
			} else {
				if (!this._username.isValid()) {
					this._username.focusInvalid();
				} else if (!this._password.isValid()) {
					this._password.focusInvalid();
				}
			}
		},

		getCredentials: function() {
			if (this._forceLoginChange && this.allowAuthenticated()) {
				return {};
			}
			return {
				'username': this._username.get('value'),
				'password': this._password.get('value')
			};
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

					this._deleteAccountButton = null;
					if (tools.isTrue(tools.status('umc/self-service/account-deregistration/enabled'))) {
						this._deleteAccountButton = new Button({
							label: _('Delete my account'),
							callback: lang.hitch(this, '_deleteAccount')
						});
					}

					this._cancelButton = new Button({
						label: _('Cancel'),
						callback: lang.hitch(this, '_deleteUserAttributesStep')
					});

					put(this._userAttributesStep, this._form.domNode);
					var buttonRow = put(this._userAttributesStep, 'div.umcPageFooter');
					var buttonsLeft = put(buttonRow, 'div.umcPageFooterLeft');
					var buttonsRight= put(buttonRow, 'div.umcPageFooterRight');
					put(buttonsLeft, this._cancelButton.domNode);
					if (this._deleteAccountButton) {
						put(buttonsRight, this._deleteAccountButton.domNode);
					}
					put(buttonsRight, this._saveButton.domNode);

					on(this._form, 'valuesInitialized', lang.hitch(this, function() {
						this._form.setFormValues(data.values);
						this._form.ready()
							.then(lang.hitch(this, function() {
								this._initialFormValues = this._form.get('value');
								this.standby(false);
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
			this.standby(true);
			var data = this.getCredentials();
			data.attributes = alteredValues;
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
						.always(lang.hitch(this, 'standby', false));
				}))
				.otherwise(lang.hitch(this, 'standby', false));
		},

		_deleteUserAttributesStep: function() {
			put(this._userAttributesStep, '!');
			this._form.destroyRecursive();

			this._username.reset();
			this._password.reset();
			this._getUserAttributesButton.show();
		},

		_deleteAccount: function() {
			var data = {
				username: this._username.get('value'),
				password: this._password.get('value')
			};
			dialog.confirm(_('Do you really want to delete your account?'), [{
				label: 'Cancel',
				name: 'cancel',
				default: true
			}, {
				label: _('Delete my account'),
				name: 'delete',
				callback: lang.hitch(this, function() {
					var deferred = tools.umcpCommand('passwordreset/deregister_account', data)
						.then(lang.hitch(this, function() {
							this._deleteUserAttributesStep();
							window.requestAnimationFrame(function() {
								dialog.alert(_('Your account has been successfully deleted.'));
							});
						}));
					this.standbyDuring(deferred);
				})
			}]);
		}
	};
});
