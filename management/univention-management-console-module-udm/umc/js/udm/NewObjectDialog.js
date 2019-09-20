/*
 * Copyright 2011-2019 Univention GmbH
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
	"dojo/topic",
	"dojo/promise/all",
	"dojo/Deferred",
	"dijit/Dialog",
	"dijit/layout/StackContainer",
	"umc/tools",
	"umc/widgets/StandbyMixin",
	"umc/modules/udm/cache",
	"umc/modules/udm/wizards/FirstPageWizard",
	"umc/modules/udm/NotificationText",
	"umc/modules/udm/UsernameMaxLengthChecker",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, topic, all, Deferred, Dialog, StackContainer, tools, StandbyMixin, cache, FirstPageWizard, NotificationText, UsernameMaxLengthChecker, _) {

	return declare("umc.modules.udm.NewObjectDialog", [ Dialog, StandbyMixin ], {
		// summary:
		//		Dialog class for creating a new LDAP object.

		'class': 'umcUdmNewObjectDialog umcLargeDialog',

		// umcpCommand: Function
		//		Reference to the module specific umcpCommand function.
		umcpCommand: null,

		// moduleFlavor: String
		//		Specifies the flavor of the module. This property is necessary to decide what
		//		kind of dialog is presented: in the context of a particular UDM module or
		//		the UDM navigation.
		moduleFlavor: '',

		// selectedContainer: Object
		//		If the new object shall be placed into a container that is specified
		//		upfront, the container (with id [=ldap-dn], label, and path [=LDAP path])
		//		can be specified via this property.
		selectedContainer: { id: '', label: '', path: '' },

		// selectedSuperordinate: Object
		// Superordinate object (with id [=ldap-dn], label, and path [=LDAP path], objectType)
		selectedSuperordinate: null,

		// defaultObjectType: String
		//		The object type that is selected by default.
		defaultObjectType: null,

		showObjectType: true,
		showObjectTemplate: true,

		autofocus: false, // interferes with Wizard.autoFocus

		_notificationText: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			var _titleText = lang.hitch(this, function() {
				var text = {
					'users/user'          : _('Add a new user.'),
					'groups/group'        : _('Add a new group.'),
					'computers/computer'  : _('Add a new computer.'),
					'networks/network'    : _('Add a new network object.'),
					'dns/dns'             : _('Add a new DNS object.'),
					'dhcp/dhcp'           : _('Add a new DHCP object.'),
					'shares/share'        : _('Add a new share.'),
					'shares/print'        : _('Add a new printer.'),
					'mail/mail'           : _('Add a new mail object.'),
					'nagios/nagios'       : _('Add a new Nagios object.'),
					'policies/policy'     : _('Add a new policy.'),
					'settings/portal_all' : _('Add a new portal object.')
				}[this.moduleFlavor];
				if (!text) {
					text = _('Add a new LDAP object.');
				}
				return text;
			});
			this.canContinue = new Deferred();
			this.createWizardAdded = new Deferred();
			this._readyForCreateWizard = new Deferred();

			// mixin the dialog title
			lang.mixin(this, {
				title: _titleText()
			});
		},

		buildRendering: function() {
			this.inherited(arguments);

			var deferred;
			if ('navigation' === this.moduleFlavor) {
				deferred = new Deferred();
				deferred.resolve([]);
			} else {
				deferred = this.moduleCache.getTemplates();
			}
			deferred.then(lang.hitch(this, function(templates) {
				var defaultTemplate = null;
				if ('navigation' != this.moduleFlavor && templates.length) {
					var initialValue = this.defaultObjectType;
					if (initialValue) {
						var match = array.filter(templates, function(ielement) {
							return ielement.id == initialValue ||
								ielement.label.toLowerCase() == initialValue.toLowerCase();
						});
						if (match.length) {
							defaultTemplate = match[0].id;
						}
					}
				}
				this._renderForm(defaultTemplate);
			}));
		},

		_renderForm: function(defaultTemplate) {
			this._wizardContainer = new StackContainer({});
			this._preWizard = new FirstPageWizard({
				title: this.get('title'),
				defaultObjectType: this.defaultObjectType,
				defaultTemplate: defaultTemplate,
				moduleCache: this.moduleCache,
				moduleFlavor: this.moduleFlavor,
				umcpCommand: this.umcpCommand,
				selectedContainer: this.selectedContainer,
				selectedSuperordinate: this.selectedSuperordinate,
				showObjectTemplate: this.showObjectTemplate,
				showObjectType: this.showObjectType,
				standby: lang.hitch(this, 'standby'),
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});

			this._preWizard.canContinue().then(lang.hitch(this, function() {
				this.canContinue.resolve();
			}), lang.hitch(this, function() {
				this.canContinue.reject();
			}));

			this._wizardContainer.addChild(this._preWizard);
			this._wizardContainer.startup();
			this._wizardContainer.selectChild(this._preWizard);
			this.own(this._wizardContainer);

			this.set('content', this._wizardContainer);

			this._preWizard.on('Cancel', lang.hitch(this, function() {
				this.hide();
			}));

			this._notificationText = new NotificationText();
			this.own(this._notificationText);
			this.addChild(this._notificationText, 0);

			var createWizard = lang.hitch(this, function() {
				var firstPageValues = this._preWizard.getValues();
				var objectTypeName = this._preWizard.getObjectTypeName();
				this.mayCreateWizard.then(lang.hitch(this, function() {
					this.buildCreateWizard(firstPageValues, objectTypeName);
				}));
			});
			this._preWizard.on('Finished', createWizard);  // the wizard either finished by hand
			this.canContinue.then(createWizard);  // or it should not be displayed at all (onFinished was immediately fired so we missed the event)
			// TODO: replace event by deferred to make it stable because: The order here is important: 1. selectChild(this._preWizard) 2. _preWizard.on('Finished', createWizard)
			// otherwise the prewidget gets selected after the real wizard has been selected so that the wrong wizard is shown
			this.canContinue.then(undefined, lang.hitch(this._preWizard, 'selectCorrectChild'));


		},

		buildCreateWizard: function(firstPageValues, objectTypeName) {
			var wizardDeferred = this.moduleCache.getWizard(firstPageValues.objectType || this.moduleFlavor);
			if (this.wizardsDisabled) {
				wizardDeferred = new Deferred();
				wizardDeferred.reject();
			}
			this._readyForCreateWizard = new Deferred();
			this.standbyDuring(all([this.createWizardAdded, wizardDeferred]));
			this.onFirstPageFinished(firstPageValues);

			wizardDeferred.then(
				lang.hitch(this, function(WizardClass) {
					this._readyForCreateWizard.then(lang.hitch(this, function(detailsValues) {
						var createWizard = new WizardClass({
							umcpCommand: this.umcpCommand,
							objectTypeName: objectTypeName,
							detailPage: detailsValues.detailPage,
							template: detailsValues.template,
							preWizardAvailable: this.canContinue.isRejected(),
							properties: detailsValues.properties,
							autoHeight: true
						});
						if (this.moduleFlavor === 'users/user') {
							new UsernameMaxLengthChecker({textBoxWidget: createWizard.getWidget('username')});
						}
						// insert at position 1. If another createWizard is added
						//   (after successfully saving the object) that
						//   wizard is also insert at 1, and removing this createWizard will
						//   selectChild(that_wizard), not firstPageWizard
						this._wizardContainer.addChild(createWizard, 1);
						this._wizardContainer.selectChild(createWizard);
						this.createWizardAdded.resolve();
						var finishWizard = lang.hitch(this, function(wizardFormValues, submit) {
							this.standbyDuring(detailsValues.detailPage.ready()).then(lang.hitch(this, function() {
								lang.mixin(detailsValues.detailPage.templateObject._userChanges, createWizard.templateObject._userChanges);
								tools.forIn(wizardFormValues, lang.hitch(this, function(key, val) {
									detailsValues.detailPage._form.getWidget(key).set('value', val);
								}));
								createWizard.setCustomValues(wizardFormValues, detailsValues.detailPage._form);
								if (submit) {
									detailsValues.detailPage._form.ready().then(lang.hitch(this, function() {
										var saveDeferred = detailsValues.detailPage.save();
										if (saveDeferred.then) {
											this.standbyDuring(saveDeferred);
											saveDeferred.then(
												lang.hitch(this, function() {
													this._notificationText.showSuccess(_('The %s has been created.', createWizard.objectName()));
													this.createWizardAdded = new Deferred();
													this.buildCreateWizard(firstPageValues, objectTypeName);
													this.createWizardAdded.then(lang.hitch(this, function() {
														// new createWizard added, now we can remove this one
														this._wizardContainer.removeChild(createWizard);
														createWizard.destroyRecursive();
													}));
												}),
												lang.hitch(this, function() {
													this.onDone();
												})
											);
										} else {
											this.onDone();
										}
									}));
								} else {
									this.onDone();
								}
							}));
						});
						createWizard.on('BackToFirstPage', lang.hitch(this, function() {
							this.createWizardAdded = new Deferred();
							this._preWizard.selectCorrectChild();
							this._wizardContainer.selectChild(this._preWizard);
							this._wizardContainer.removeChild(createWizard);
							createWizard.destroyRecursive();
						}));
						createWizard.on('Advanced', lang.hitch(this, function(values) {
							topic.publish('/umc/actions', 'udm', this.moduleFlavor, 'create-wizard', 'advance');
							finishWizard(values, false);
						}));
						createWizard.on('Cancel', lang.hitch(this, function() {
							topic.publish('/umc/actions', 'udm', this.moduleFlavor, 'create-wizard', 'cancel');
							this.hide().then(function() {
								detailsValues.detailPage.onCloseTab();
							});
						}));
						createWizard.on('Finished', lang.hitch(this, function(values) {
							finishWizard(values, true);
						}));
					}));
				}), lang.hitch(this, function() {
					this.createWizardAdded.reject();
					this.onDone();
				})
			);
		},

		focusNextOnFirstPage: function() {
			this._preWizard.focusFirstWidget('firstPage');
		},

		setDetails: function(detailPage, template, properties) {
			this._readyForCreateWizard.resolve({
				detailPage: detailPage,
				template: template,
				properties: properties
			});
		},

		onDone: function() {
			// event stub
		},

		onCancel: function() {
		},

		onFirstPageFinished: function(values) {
		}
	});
});
