/*
 * Copyright 2020-2022 Univention GmbH
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
	"dojo/dom-construct",
	"dojo/on",
	"dojox/html/entities",
	"umc/render",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Form",
	"put-selector/put",
	"umc/i18n/tools",
	"umc/i18n!."
], function(lang, array, Deferred, domConstruct, on, entities, render, tools, dialog, Form, put, i18nTools, _) {

	return {
		hash: 'createaccount',
		enabledViaUcr: 'umc/self-service/account-registration/frontend/enabled',
		visible: true,

		title: _('Create an account'),
		contentContainer: null,

		_loadingDeferred: null,

		startup: function() {
			this.standbyDuring(this._loadingDeferred);
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

			// create user
			var creationDeferred = new Deferred();
			this.standbyDuring(creationDeferred);
			tools.umcpCommand('passwordreset/create_self_registered_account', { attributes: this._form.get('value') })
				.then(lang.hitch(this, function(res) {
					res = res.result;
					if (!res.success) {
						switch (res.failType) {
							case 'INVALID_ATTRIBUTES':
								this._form.setValid(res.data);
								this._form.focusFirstInvalidWidget();
								break;
							case 'CREATION_FAILED':
								dialog.alert('<p class="umcServerErrorMessage">' + entities.encode(res.data).replace(/\n/g, '<br/>') + '</p>');
								break;
						}
					} else {
						this._createVerificationMessage(res.verifyTokenSuccessfullySend, res.data);
					}
				}))
				.always(function() {
					creationDeferred.resolve();
				});
		},

		_createVerificationMessage: function(verifyTokenSuccessfullySend, data) {
			this._form.destroyRecursive();
			var msg = '';
			if (verifyTokenSuccessfullySend) {
				msg = _('Hello <b>%s</b>, we have sent you an email to <b>%s</b>. Please follow the instructions in the email to verify your account.', entities.encode(data.username), entities.encode(data.email));
			} else {
				msg = _('An error occurred while sending the verification token for your account. Please <a href="#page=verifyaccount&username=%s">request a new one</a>.', entities.encode(data.username));
			}
			msg = domConstruct.toDom(msg);
			msg = put('p', msg);
			put(this.contentContainer, msg);
		}
	};
});

