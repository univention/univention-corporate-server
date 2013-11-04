/*
 * Copyright 2013 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/query",
	"dojo/parser",
	"dojo/dom-attr",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/Deferred",
	"dojo/when",
	"dojo/topic",
	"dijit/registry",
	"dijit/Dialog",
	"dijit/layout/StackContainer",
	"dijit/form/RadioButton",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Button",
	"umc/i18n!umc/app"
], function(declare, lang, kernel, array, query, parser, domAttr, domClass, domGeometry, Deferred, when, topic, registry, Dialog, StackContainer, RadioButton, tools, dialog, Text, ContainerWidget, Button, _) {
	var _lang = kernel.locale.split('-')[0];
	var _getDocumentDependency = function(key) {
		return lang.replace('dojo/text!umc/app/{key}.{lang}.html', {
			key: key,
			lang: _lang
		});
	};

	var isLicenseActivated = function() {
		return tools.ucr('uuid/license').then(function(ucr) {
			return Boolean(ucr['uuid/license']);
		});
	}

	var _docDeferred = new Deferred();
	var preloadTemplateDocuments = function() {
		isLicenseActivated().then(function(activated) {
			var docs = ['welcome', 'feedback', 'activation', 'help', 'finished'];
			if (activated) {
				// remove license activation page if system is already activated
				var indexActivation = array.indexOf(docs, 'activation');
				if (indexActivation >= 0) {
					docs.splice(indexActivation, 1);
				}
			}

			// pre-load HTML template documents
			var _docDependencies = array.map(docs, _getDocumentDependency);
			require(_docDependencies, function(/*...*/) {
				_docDeferred.resolve(arguments);
			});
		});
	};

	preloadTemplateDocuments();


	var _replaceVariablesInDocument = function(piwikDisabled, doc) {
		return lang.replace(doc, {
			path: require.toUrl('umc/app'),
			feedbackUrl: _('umcFeedbackUrl'),
			hardwareStatisticsCheckboxDisplay: 'block',
			version: tools.status('ucsVersion').split('-')[0]
		});
	};

	return declare(Dialog, {
		// summary:
		//		The dialog which is shown during the first login of Administrator.

		title: _('Welcome to UMC'),

		_stackContainer: null,

		_pages: null,

		_wizardCompleted: false,

		buildRendering: function() {
			this.inherited(arguments);

			this._stackContainer = new StackContainer({
				'class': 'umcPopup'
			});

			this._pages = [];
			when(_docDeferred, lang.hitch(this, function(_docs) {
				// note that way can only access 'piwikDisabled' here, as we cannot
				// be sure that the variable has been set before (in umc/app)
				var docs = array.map(_docs, lang.hitch(this, _replaceVariablesInDocument, tools.status('piwikDisabled')));
				array.forEach(docs, function(idoc, idx) {
					// build footer
					var footer = new ContainerWidget({
						'class': 'umcPageFooter',
						style: 'overflow:auto;'
					});

					var footerRight = new ContainerWidget({
						style: 'float:right;'
					});

					// 'cancel' button
					if (idx < docs.length - 1) {
						footer.addChild(new Button({
							label: _('Cancel'),
							callback: lang.hitch(this, 'close', false),
							style: 'float:left'
						}));
					}

					// 'back' button
					if (idx > 0) {
						footerRight.addChild(new Button({
							label: _('Back'),
							callback: lang.hitch(this, '_gotoPage', idx - 1)
						}));
					}

					// 'next' button
					if (idx < docs.length - 1) {
						footerRight.addChild(new Button({
							label: _('Next'),
							callback: lang.hitch(this, '_gotoPage', idx + 1, idx),
							defaultButton: true
						}));
					}

					// 'close' button
					if (idx == docs.length - 1) {
						footerRight.addChild(new Button({
							label: _('Close'),
							callback: lang.hitch(this, 'close', true),
							defaultButton: true
						}));
					}
					footer.addChild(footerRight);

					// create 'page'
					var page = new ContainerWidget({});
					var html = new Text({
						content: idoc,
						style: 'width:600px; max-height:280px; overflow-y:auto; overflow-x:hidden;'
					});
					parser.parse(html.domNode);
					page.addChild(html);
					page.addChild(footer);
					this._pages.push(page);
					this._stackContainer.addChild(page);
				}, this);

				this._adjustWizardHeight();
			}));

			this.on('hide', lang.hitch(this, function() {
				this._evaluate();
				setTimeout(lang.hitch(this, 'destroyRecursive'), 0);
			}));
		},

		_adjustWizardHeight: function() {
			domClass.add(this.domNode, 'dijitOffScreen');
			this.show();
			var height = this._getMaxHeight();
			array.forEach(this._pages, function(ipage) {
				var icontent = ipage.getChildren()[0];
				domGeometry.setMarginBox(icontent.domNode, { h: height });
			});
			domClass.remove(this.domNode, 'dijitOffScreen');
			this._position();
		},

		_getMaxHeight: function() {
			this.set('content', this._stackContainer);
			var heights = array.map(this._pages, lang.hitch(this, function(ipage) {
				this._stackContainer.selectChild(ipage);
				var icontent = ipage.getChildren()[0];
				return domGeometry.getMarginBox(icontent.domNode).h;
			}));
			this._stackContainer.selectChild(this._pages[0]);
			return Math.max.apply(window, heights);
		},

		close: function(closed) {
			this._wizardCompleted = closed;
			this.hide();
		},

		destroyRecursive: function() {
			this.inherited(arguments);
		},

		_gotoPage: function(idx, oldIdx) {
			if (oldIdx >= 0 && query('#umc_app_activation_email', this._pages[oldIdx].domNode).length) {
				// activiation page is visible
				if (this._isValidEmail() === false) {
					dialog.alert(_('Please enter a valid email address!'));
					return;
				}
			}
			this._stackContainer.selectChild(this._pages[idx]);
		},

		_evaluate: function() {
			if (this._wizardCompleted) {
				this._evaluateFeedback();
				this._evaluateHardwareStatistics();
				this._evaluateActivation();
			}
			this._evaluateWizardCompleted();
		},

		_evaluateFeedback: function() {
			var installationOK = registry.byId('umc_app_startup_installation_ok').get('value');
			var installationNotOK = registry.byId('umc_app_startup_installation_not_ok').get('value');
			var label = 'none';
			if (installationOK || installationNotOK) {
				label = installationOK ? 'positive' : 'negative';
			}
			topic.publish('/umc/actions', 'startup-wizard', 'installation-feedback', label)
		},

		_evaluateHardwareStatistics: function() {
			var enableHardwareStatistics = registry.byId('umc_app_feedback_Checkbox').get('checked');
			if (enableHardwareStatistics) {
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
			}
		},

		_getEmail: function() {
			var emailWidget = registry.byId('umc_app_activation_email');
			if (!emailWidget) {
				return null;
			}
			return emailWidget.get('value');
		},

		_isValidEmail: function() {
			var emailWidget = registry.byId('umc_app_activation_email');
			if (!emailWidget) {
				return null;
			}
			var email = emailWidget.get('value');
			if (!email) {
				return null;
			}
			return emailWidget.isValid();
		},

		_evaluateActivation: function() {
			if (this._isValidEmail()) {
				tools.umcpCommand('udm/request_new_license', {
					email: this._getEmail()
				}, false).then(function() {}, lang.hitch(this, function() {
					dialog.alert(_('The activation of UCS failed. Please re-try to perform the the activation again via the settings menu.'));
				}));
			}
		},

		_evaluateWizardCompleted: function() {
			var label = this._wizardCompleted ? 'completed' : 'canceled';
			topic.publish('/umc/actions', 'startup-wizard', label);
		}
	});
});

