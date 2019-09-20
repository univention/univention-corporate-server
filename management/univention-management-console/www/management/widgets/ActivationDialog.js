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
	"dojo/dom-class",
	"dojo/when",
	"dojo/topic",
	"dijit/Dialog",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Wizard",
	"umc/widgets/Text",
	"umc/widgets/ProgressBar",
	"umc/widgets/StandbyMixin",
	"./ActivationPage!",  // needs to be loaded as AMD plugin
	"./LicenseImportPage!",  // needs to be loaded as AMD plugin
	"./FinishedActivationPage",
	"umc/i18n!management"
], function(declare, lang, array, domClass, when, topic, Dialog, tools, dialog, Wizard, Text, ProgressBar,
		StandbyMixin, ActivationPage, LicenseImportPage, FinishedActivationPage, _) {

	return declare([Dialog, StandbyMixin], {
		// summary:
		//		The dialog which is shown during the first login of Administrator.

		title: _('Activation of Univention Corporate Server'),

		'class': 'umcStartupDialog umcActivationDialog umcLargeDialog',

		_wizard: null,

		_wizardCompleted: false,

		_progressBar: null,

		// specifies only those pages that shall be rendered
		visiblePages: null,

		buildRendering: function() {
			this.inherited(arguments);

			// some pages might return null
			var pages = [ActivationPage, LicenseImportPage, FinishedActivationPage];
			var thisDialog = this;
			this._wizard = new Wizard({
				pages: pages,
				autoHeight: true,
				autoValidate: true,
				onFinished: lang.hitch(this, 'hide'),
				onCancel: lang.hitch(this, 'hide')
			});

			// create a progress bar widget
			this._progressBar = new ProgressBar({});
			this.own(this._progressBar);

			// safeMixin() is needed here for this.inherited() to work correctly
			declare.safeMixin(this._wizard, {
				next: function(pageName) {
					topic.publish('/umc/actions', 'activation-wizard', pageName, 'next');
					var nextPage = this.inherited(arguments);
					if (pageName != 'activation') {
						return nextPage;
					}
					var deferred = when(lang.hitch(thisDialog, '_evaluateActivation')()).then(function(success) {
						// only advance if no error occurred
						var actionLabel = success === true ? 'success' : 'failure';
						topic.publish('/umc/actions', 'activation-wizard', 'activation', actionLabel);
						return success ? nextPage : pageName;
					});
					thisDialog._progressBar.setInfo(_('Sending activation email...'), null, Infinity);
					thisDialog.standbyDuring(deferred, thisDialog._progressBar);
					return deferred;
				},

				previous: function(pageName) {
					topic.publish('/umc/actions', 'activation-wizard', pageName, 'previous');
					return this.inherited(arguments);
				},

				canCancel: function(pageName) {
					return pageName != 'finished';
				},

				hasPrevious: function(pageName) {
					return pageName == 'licenseImport';
				},

				_updateButtons: function(pageName) {
					this.inherited(arguments);

					// hide next button on license import page
					var buttons = this._pages[pageName]._footerButtons;
					if (pageName == 'licenseImport') {
						domClass.add(buttons.next.domNode, 'dijitDisplayNone');
						domClass.add(buttons.previous.domNode, 'dijitDisplayNone');
					}
				}
			});

			// adjust the label of the next button on the first page
			var buttons = this._wizard._pages.activation._footerButtons;
			buttons.next.set('label', _('Send license'));

			// register wizard logic for license upload
			// (standby animation + go to next page)
			var licenseUploader = this._wizard.getWidget('licenseImport', 'licenseUpload');
			licenseUploader.onImportLicense = lang.hitch(this, function(deferred) {
				this._progressBar.setInfo(_('Importing license data...'), null, Infinity);
				topic.publish('/umc/actions', 'activation-wizard', 'licenseImport', 'upload');
				this.standbyDuring(deferred, this._progressBar);
				deferred.then(lang.hitch(this, function() {
					// activation has been successful -> close dialogue
					topic.publish('/umc/actions', 'activation-wizard', 'licenseImport', 'success');
					this._wizard._next('licenseImport');
				}), function(errMsg) {
					topic.publish('/umc/actions', 'activation-wizard', 'licenseImport', 'failure');
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

			this.on('hide', lang.hitch(this, 'destroyRecursive'));
		},

		postCreate: function() {
			this.inherited(arguments);
			this.show();
		},

		_evaluateActivation: function() {
			var emailWidget = this._wizard.getWidget('activation', 'email');
			var email = lang.trim(emailWidget.get('value'));
			if (!email) {
				return false;
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
		}
	});
});

