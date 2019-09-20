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
/*global define setTimeout console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/when",
	"dojo/topic",
	"dijit/Dialog",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Wizard",
	"umc/widgets/Text",
	"umc/widgets/ProgressBar",
	"./WelcomePage",
	"./FeedbackPage",
	"./ActivationPage!",  // needs to be loaded as AMD plugin
	"./LicenseImportPage!",  // needs to be loaded as AMD plugin
	"./HelpPage",
	"./FinishedPage",
	"umc/i18n!management"
], function(declare, lang, array, when, topic, Dialog, tools, dialog, Wizard, Text, ProgressBar,
		WelcomePage, FeedbackPage, ActivationPage, LicenseImportPage, HelpPage, FinishedPage, _) {

	return declare(Dialog, {
		// summary:
		//		The dialog which is shown during the first login of Administrator.

		title: _('Welcome to UMC'),

		'class': 'umcStartupDialog umcLargeDialog',

		_wizard: null,

		_wizardCompleted: false,

		_progressBar: null,

		buildRendering: function() {
			this.inherited(arguments);

			// some pages might return null
			var pages = [WelcomePage, FeedbackPage, ActivationPage, LicenseImportPage, HelpPage, FinishedPage];
			var thisDialog = this;
			this._wizard = new Wizard({
				pages: pages,
				autoHeight: true,
				autoValidate: true,
				onFinished: lang.hitch(this, 'close', true),
				onCancel: lang.hitch(this, 'close', false)
			});

			this._wizard.getWidget('feedback', 'enableHardwareStatistics').set('visible', true);

			// create a progress bar widget
			this._progressBar = new ProgressBar({});
			this.own(this._progressBar);

			// safeMixin() is needed here for this.inherited() to work correctly
			declare.safeMixin(this._wizard, {
				isPageVisible: function(pageName) {
					var page = this._pages[pageName];
					if (typeof page.showInStartupDialog == 'function') {
						return page.showInStartupDialog(this.getValues());
					}
					return page.showInStartupDialog !== false;
				},

				next: function(pageName) {
					topic.publish('/umc/actions', 'startup-wizard', pageName, 'next');
					var nextPage = this.inherited(arguments);
					var deferred = null;
					if (pageName == 'activation') {
						deferred = when(lang.hitch(thisDialog, '_evaluateActivation')()).then(function(success) {
							// only advance if no error occurred
							var actionLabel = success === true ? 'success' : success === false ? 'failure' : 'empty-email';
							topic.publish('/umc/actions', 'startup-wizard', 'activation', actionLabel);
							return success !== false ? nextPage : 'help';
						});
						thisDialog._progressBar.setInfo(_('Sending activation email...'), null, Infinity);
						this.standbyDuring(deferred, thisDialog._progressBar);
						return deferred;
					}
					return nextPage;
				},

				previous: function(pageName) {
					topic.publish('/umc/actions', 'startup-wizard', pageName, 'previous');
					return this.inherited(arguments);
				}
			});

			// register wizard logic for license upload
			// (standby animation + go to next page)
			var licenseUploader = this._wizard.getWidget('licenseImport', 'licenseUpload');
			licenseUploader.onImportLicense = lang.hitch(this, function(deferred) {
				this._progressBar.setInfo(_('Importing license data...'), null, Infinity);
				topic.publish('/umc/actions', 'startup-wizard', 'licenseImport', 'upload');
				this._wizard.standbyDuring(deferred, this._progressBar);
				deferred.then(lang.hitch(this, function() {
					// advance to next page
					topic.publish('/umc/actions', 'startup-wizard', 'licenseImport', 'success');
					this._wizard._next('licenseImport');
				}), function(errMsg) {
					topic.publish('/umc/actions', 'startup-wizard', 'licenseImport', 'failure');
					var msg = '<p>' + _('The import of the license failed. Check the integrity of the original file given to you.') + '</p>';
					if (errMsg) {
						msg += '<p>' + _('Server error message:') + '</p><p class="umcServerErrorMessage">' + errMsg + '</p>';
					}
					dialog.alert(msg);
				}, lang.hitch(this._progressBar, 'setInfo'));
			});

			// add CSS classes per page, add icon element
			array.forEach(pages, function(ipageConf) {
				var ipage = this._wizard._pages[ipageConf.name];
				ipage.addChild(new Text({
					'class': 'umcPageIcon',
					region: 'nav'
				}));
			}, this);

			this.addChild(this._wizard);

			this._wizard.watch('selectedChildWidget', lang.hitch(this, function(name, old, child) {
				this.set('title', child.headerText);
			}));

			this.on('hide', lang.hitch(this, function() {
				this._evaluate();
				setTimeout(lang.hitch(this, 'destroyRecursive'), 0);
			}));
		},

		postCreate: function() {
			this.inherited(arguments);
			this.show();
		},

		close: function(closed) {
			this._wizardCompleted = closed;
			this.hide();
		},

		_evaluate: function() {
			if (this._wizardCompleted) {
				this._evaluateFeedback();
				this._evaluateHardwareStatistics();
			}
			this._evaluateWizardCompleted();
		},

		_getValue: function(page, widgetName) {
			var widget = this._wizard.getWidget(page, widgetName);
			if (!widget) {
				return null;
			}
			return widget.get('value');
		},

		_evaluateFeedback: function() {
			var installationOK = this._getValue('welcome', 'installation_ok');
			var installationNotOK = this._getValue('welcome', 'installation_not_ok');
			var label = 'none';
			if (installationOK || installationNotOK) {
				label = installationOK ? 'positive' : 'negative';
			}
			topic.publish('/umc/actions', 'startup-wizard', 'installation-feedback', label);
		},

		_evaluateHardwareStatistics: function() {
			var enableHardwareStatistics = this._getValue('feedback', 'enableHardwareStatistics');
			if (!enableHardwareStatistics) {
				return;
			}

			tools.umcpCommand('sysinfo/general', {}, false).then(function(response) {
				var options = response.result;
				options.comment = 'Sent via UMC startup wizard.';
				return tools.umcpCommand('sysinfo/system', options, false);
			}).then(function(response) {
				// upload archive
				return tools.umcpCommand('sysinfo/upload', {
					archive: response.result.archive
				}, false);
			}).then(function() {}, function() {
				// silently ignore errors
				console.log('Hardware information could not be sent.');
			});
		},

		_evaluateActivation: function() {
			var emailWidget = this._wizard.getWidget('activation', 'email');
			var email = lang.trim(emailWidget.get('value'));
			if (!email) {
				return;
			}

			return tools.umcpCommand('udm/request_new_license', {
				email: email
			}, false).then(function() {
				return true;
			}, lang.hitch(this, function() {
				emailWidget.set('value', '');
				dialog.alert(_('The activation of UCS failed. Please re-try to perform the the activation again via the user menu in the top right.'));
				return false;
			}));
		},

		_evaluateWizardCompleted: function() {
			var label = this._wizardCompleted ? 'completed' : 'canceled';
			topic.publish('/umc/actions', 'startup-wizard', label);
		}
	});
});

