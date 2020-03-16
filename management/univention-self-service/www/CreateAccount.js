/*
 * Copyright 2020 Univention GmbH
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
	"dojo/Deferred",
	"dojo/on",
	"dojox/html/entities",
	"umc/render",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Form",
	"put-selector/put",
	"umc/i18n!."
], function(lang, array, Deferred, on, entities, render, tools, dialog, Form, put, _) {

	return {
		hash: 'createaccount',
		enabledViaUcr: 'umc/self-service/registration/enabled',
		visible: true,

		title: _('Create an account'),
		contentContainer: null,

		_loadingDeferred: null,

		startup: function() {
			this.standbyDuring(this._loadingDeferred);
		},

		getTitle: function() {
			return this.title;
		},

		getContent: function() {
			if (!this.contentContainer) {
				this.contentContainer = put('div.contentWrapper');
				put(this.contentContainer, 'h2', this.title);
				this._createForm();
			}
			return this.contentContainer;
		},

		_createForm: function() {
			this._loadingDeferred = new Deferred();
			tools.umcpCommand('passwordreset/get_registration_attributes').then(lang.hitch(this, function(data) {
				data = data.result;
				var widgetDescriptions = this._prepareWidgets(data.widget_descriptions);
				render.requireWidgets(widgetDescriptions)
					.then(lang.hitch(this, function() {
						this._form = new Form({
							widgets: widgetDescriptions,
							layout: data.layout,
							buttons: [{
								'class': 'createaccount__submitbutton umcFlatButton',
								label: _('Create account'),
								name: 'submit'
							}],
							onSubmit: lang.hitch(this, '_createAccount')
						});
						put(this.contentContainer, this._form.domNode);
						on(this._form, 'valuesInitialized', lang.hitch(this, function() {
							this._loadingDeferred.resolve();
						}));
						this._form.startup();
					}));
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

		_createAccount: function() {
			this._form.setValid(null);

			// frontend validation (like valid choice in ComboBox)
			if (!this._form.validate()) {
				this._form.focusFirstInvalidWidget();
				return;
			}

			// backend validation
			var creationDeferred = new Deferred();
			this.standbyDuring(creationDeferred);
			var data = {
				attributes: this._form.get('value')
			};
			tools.umcpCommand('passwordreset/validate_registration_attributes', data)
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
					// create account
					return tools.umcpCommand('passwordreset/create_self_registered_account', data, false)
						.then(lang.hitch(this, function() {
							this._createVerificationStep(data.attributes.PasswordRecoveryEmail);
						}), function(error) {
							var info = tools.parseError(error);
							if (info.message.startsWith(_('The account could not be created'))) {
								var message = info.message;
								dialog.alert('<p class="umcServerErrorMessage">' + entities.encode(message).replace(/\n/g, '<br/>') + '</p>');
							} else {
								var errorHandler = tools.__getErrorHandler(true);
								errorHandler.error(info);
							}
						});
				}))
				.always(function() {
					creationDeferred.resolve();
				});
		},

		_createVerificationStep: function(email) {
			this._form.destroyRecursive();
			var msg = _('An email has been sent to %s. Please follow the instructions in the email to verify your account.', entities.encode(email));
			put(this.contentContainer, 'div.createaccount__verificationmsg', msg);
		}
	};
});

