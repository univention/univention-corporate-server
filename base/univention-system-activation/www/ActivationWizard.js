/*
 * Copyright 2017-2019 Univention GmbH
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
	"dojo/_base/array",
	"dojo/Deferred",
	"dojo/io-query",
	"dojo/query",
	"dojo/request",
	"dojo/request/xhr",
	"dojo/request/script",
	"dojox/form/Uploader",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Wizard",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"put-selector/put",
	"umc/i18n!systemactivation"
], function(declare, lang, array, Deferred, ioQuery, domQuery, request, xhr, script, Uploader, dialog, tools, Wizard, Text, TextBox, put, _) {
	return declare("ActivationWizard", [ Wizard ], {
		autoFocus: true,
		entries: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			var version = '4.4';
			lang.mixin(this, {
				pages: [{
					name: 'register',
					headerText: _('License request for %(appliance_name)s Appliance', this.entries),
					widgets: [{
						type: Text,
						content: _('Please enter a valid email address in order to activate %(appliance_name)s Appliance. The activation is mandatory to deploy the system. In the next step you can upload the license file that has been sent to your email address.', this.entries),
						name: 'helpText'
					}, {
						type: TextBox,
						inlineLabel: _('E-mail address'),
						regExp: '.+@.+',
						invalidMessage: _('No valid email address.'),
						required: true,
						name: 'email'
					}, {
						type: Text,
						content: _('More details about the activation can be found in the <a href="https://docs.software-univention.de/manual-%s.html#central:license" target="_blank">UCS manual</a>.', version),
						name: 'moreDetails'
					}, {
						type: Text,
						content:_('If you already have a license file you can <a href="#upload">skip this step and upload the license</a>.'),
						name: 'skip'
					}],
					layout: [['helpText'], ['email'], ['moreDetails'], ['skip']],
					fullWidth: true,
					// prevent default submit button to be created if no submit button is specified
					buttons: [{
						name: 'submit',
						visible: false
					}]
				}, {
					name: 'upload',
					headerText: _('Activation of %(appliance_name)s Appliance', this.entries),
					widgets: [{
						type: Text,
						content: _('A license file has been sent to <strong class="email-address">%s</strong>. This file is necessary to activate the system. For this, please carry out the following steps: <ol><li>Open the email.</li><li>Save the attachment (ucs.license) on your computer.</li><li>Click the button \'Upload license file\'.</li><li>Select the file (ucs.license) you just saved.</li><li>Confirm the selection.</li></ol>Once the activation has been finished your email address will be sent to the app provider. The app provider may contact you.', [this.entries.email || _('your email address')]),
						name: 'helpText'
					}, {
						type: Text,
						content: _('If you did not receive an email, please check your SPAM directory or <a href="#register"> request the email again</a>.'),
						name: 'back'
					}, {
						type: Uploader,
						url: '/license',
						name: 'license',
						label: _('Upload license file'),
						uploadOnSelect: true,
						getForm: function() {
							// make sure that the Uploader does not find any of our encapsulating forms
							return null;
						},
						visible: false
					}],
					layout: [['helpText'], ['back'], ['license']],
					fullWidth: true,
					buttons: [{
						name: 'submit',
						visible: false
					}]
				}, {
					name: 'finished',
					headerText: _('Activation successful!'),
					helpText: _('%(appliance_name)s Appliance is now activated. Click "Finish" to access the management interface (which may take a while).', this.entries),
					fullWidth: true
				}]
			});
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._alterPageButtons();
			this._registerEvents();
		},

		_alterPageButtons: function() {
			//rename specific buttons
			this._pages.register._footerButtons.next.set('label', _('Request activation'));

			//// add dojox.form.Uploader button to 'upload' page
			// we defined the 'upload' page to have no buttons.
			// To prevent an error in the _udpateButtons function in umc.widgets.Wizard.js
			// we set _footerButtons
			this._pages.upload._footerButtons = {
				'license': this.getWidget('upload', 'license')
			};
			// add the button dojox.form.Uploader button to the right buttons footer of the upload page
			this._pages.upload._footer.getChildren()[1].addChild(this.getWidget('upload', 'license'));
		},

		_registerEvents: function() {
			//// register Uploader events
			var uploader = this.getWidget('upload', 'license');
			uploader.on('begin', lang.hitch(this, function(evt) {
				this.standby(true);
			}));
			uploader.on('complete', lang.hitch(this, function(response) {
				this.standby(false);

				if (response && response.success) {
					// success case
					this._sendNotification(response.uuid, response.systemUUID, response.apps);
					this.onGoTo('finished');
					return;
				}

				// error case
				this._showError(response ? response.message : _('An unknown error has occurred.'));
			}));
			uploader.on('error', lang.hitch(this, function(err) {
				this.standby(false);
				this._showError(err ? err.message : _('An unknown error has occurred.'));
			}));
		},

		_sendNotification: function(uuid, systemUUID, apps) {
			var data = {
				uuid: uuid,
				'system-uuid': systemUUID,
				action: 'install',
				'status': 200,
				'role': this.entries.role
			};
			var url = this.entries.appcenter_server + '/postinst';
			if (url.indexOf('://') < 0) {
				// no scheme given
				url = 'https://' + url;
			}

			// send a notification for each app
			array.forEach(apps, function(app) {
				// data to be sent via the query string
				var idata = lang.mixin({
					app: app[0],
					version: app[1]
				}, data);

				// post cross domain query via dynamic script tag
				script(url, { query: idata });
			});
		},

		_sendEmail: function() {
			// set the email entered in the 'register' page in the help text of the 'upload' page
			var email_address = this.getWidget('register', 'email').get('value');
			var emailNode = domQuery('.email-address', this.getWidget('upload', 'helpText').domNode)[0];
			emailNode.innerHTML = email_address;

			// send the email
			return xhr.get('/license', { handleAs: 'json' }).then(function(license) {
				var data = {
					email: email_address,
					licence: license
				};
				return xhr.post('https://license.univention.de/keyid/conversion/submit', {
					data: data,
					handleAs: 'text',
					headers: {
						'X-Requested-With': null
					}
				});
			});
		},

		_checkEmail: function() {
			var emailTextBox = this.getWidget('register', 'email');
			if (!emailTextBox.isValid()){
				emailTextBox.focus();
				emailTextBox.validate();
				return false;
			}
			return true;
		},

		canCancel: function() {
			return false;
		},

		hasPrevious: function() {
			// Do not allow going backwards in the wizard.
			// Previous pages can only be visited through links in the text of a page.
			return false;
		},

		_next: function(/*String*/ pageName) {
			if (pageName === 'register') {
				var emailValid = this._checkEmail();
				if (emailValid) {
					this._sendEmail().then(lang.hitch(this, function() {
						this.onGoTo(this.next(pageName));
					}), lang.hitch(this, function(err) {
						this._showEmailError(err);
					}));
				}
			}
		},

		_showEmailError: function(err) {
			var status_code = err.response.status;
			var error_details = null;
			if (err.response.data) {
				// error from local server (univention-system-activation)
				tools.status('feedbackSubject', _('[%(appliance_name)s Appliance] Activation Error', this.entries));
				tools.handleErrorStatus(err, {hideInformVendor: true});
				return;
			} else if (status_code >= 400) {
				// error from license server
				error_details = put('html');
				error_details.innerHTML = err.response.data;
				error_details = error_details.getElementsByTagName('span')[0].innerText;
			} else {
				error_details = _('An unknown error occurred. It is possible that a browser addon blocks sending the request to "license.univention.de". More information how to avoid this error can be found <a href="https://help.univention.com/t/7698" target="_blank" rel="noreferrer noopener">in our support database</a>.');
			}
			var error_msg = _('Error ') + status_code + ': ' + error_details;
			this._showError(error_msg);
		},

		_showError: function(error_msg) {
			error_msg = error_msg.replace(/\n/g, '<br/>');
			var title = _('The following error occurred:');
			var footer = _('If you encounter problems during the activation, please send an email to: <strong><a href="mailto:feedback@univention.de" style="color:#000">feedback@univention.de</a></strong>');
			var msg = lang.replace('<p>{error_msg}</p><p>{footer}</p>', {error_msg: error_msg, footer: footer});
			dialog.alert(msg, title);
		},

		onGoTo: function(/*String*/ nextPage) {
			// stub
		},

		_finish: function() {
			var query = ioQuery.queryToObject(location.search.substring(1));
			lang.mixin(query, {
				username: 'Administrator'
			});
			this._canReachPortalWithinSecs(query, 30);
		},

		_canReachPortalWithinSecs: function(query, secs) {
			this.standby(true);
			var uri = '/univention/portal/?' + ioQuery.objectToQuery(query);

			var reachableDeferred = new Deferred();
			reachableDeferred.then(function() {
				location.href = uri;
			}, lang.hitch(this, function() {
				this.standby(false);
				this._showError(_('The server is not responding. Please restart the system.'));
			}));

			var countUntil = secs / 0.5;
			var counter = 0;
			var requestUriTillCounter = function() {
				request(uri, {
					method: 'HEAD'
				}).response.then(function(result) {
					// if uri is reachable http status code has to be 200
					if (result.status === 200) {
						reachableDeferred.resolve();
					} else { // otherwise tryAgain
						tryAgain();
					}
				},
				function(error) {
					tryAgain();
				});
			};
			var tryAgain = function() {
				if (counter >= countUntil) {
					reachableDeferred.reject();
				} else {
					setTimeout(requestUriTillCounter, 500);
				}
				counter++;
			};
			requestUriTillCounter();
		},

		getFooterButtons: function(pageName) {
			// for the 'upload' page we want the next button to be the button
			// created by dojox.form.Uploader. So we define no buttons for the upload page
			if (pageName === 'upload') {
				return [];
			}
			return this.inherited(arguments);
		}
	});
});
