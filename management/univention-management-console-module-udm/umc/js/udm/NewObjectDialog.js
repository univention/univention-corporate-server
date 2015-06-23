/*
 * Copyright 2011-2015 Univention GmbH
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
	"dojo/_base/array",
	"dojo/topic",
	"dojo/promise/all",
	"dojo/Deferred",
	"dijit/Dialog",
	"dijit/layout/StackContainer",
	"umc/tools",
	"umc/modules/udm/wizards/FirstPageWizard",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, topic, all, Deferred, Dialog, StackContainer, tools, FirstPageWizard, _) {

	return declare("umc.modules.udm.NewObjectDialog", [ Dialog ], {
		// summary:
		//		Dialog class for creating a new LDAP object.

		// umcpCommand: Function
		//		Reference to the module specific umcpCommand function.
		ucmpCommand: null,

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

		// selectedSuperordinate: String
		//		DN of the preselected superordinate.
		selectedSuperordinate: null,

		// defaultObjectType: String
		//		The object type that is selected by default.
		defaultObjectType: null,

		// LDAP object type name in singular and plural
		objectNameSingular: '',
		objectNamePlural: '',

		// force max-width
		//style: 'max-width: 300px;',

		autofocus: false, // interferes with Wizard.autoFocus

		postMixInProperties: function() {
			this.inherited(arguments);
			this.canContinue = new Deferred();
			this.createWizardAdded = new Deferred();
			this._readyForCreateWizard = new Deferred();

			// mixin the dialog title
			lang.mixin(this, {
				//style: 'max-width: 450px'
				title: _( 'Add a new %s', this.objectNameSingular )
			});
		},

		buildRendering: function() {
			this.inherited(arguments);

			if ('navigation' != this.moduleFlavor) {
				// query the necessary elements to display the add-dialog correctly
				var superordinate = this.selectedSuperordinate !== undefined ? this.selectedSuperordinate : null;
				all({
					types: this.moduleCache.getChildModules(superordinate, null, true),
					containers: this.moduleCache.getContainers().then(function(result) {
						return array.filter(result, function(icontainer) {
							return icontainer.id != 'all';
						});
					}),
					superordinates: this.moduleCache.getSuperordinates(),
					templates: this.moduleCache.getTemplates()
				}).then(lang.hitch(this, function(results) {
					var types = lang.getObject('types', false, results) || [];
					var containers = lang.getObject('containers', false, results) || [];
					var superordinates = lang.getObject('superordinates', false, results) || [];
					var templates = lang.getObject('templates', false, results) || [];
					this._renderForm(types, containers, superordinates, templates);
				}));
			} else {
				// for the UDM navigation, only query object types
				this.moduleCache.getChildModules(null, this.selectedContainer.id, true).then(lang.hitch(this, function(result) {
					this._renderForm(result);
				}));
			}
		},

		_renderForm: function(types, containers, superordinates, templates) {
			// default values and sort items
			types = types || [];
			containers = containers || [];
			superordinates = superordinates || [];
			templates = templates || [];
			array.forEach([types, containers, templates], function(iarray) {
				iarray.sort(tools.cmpObjects('label'));
			});

			this._wizardContainer = new StackContainer({
				style: 'width: 630px; height: 310px;'
			});
			this._preWizard = new FirstPageWizard({
				types: types,
				containers: containers,
				superordinates: superordinates,
				templates: templates,
				title: this.get('title'),
				defaultObjectType: this.defaultObjectType,
				moduleCache: this.moduleCache,
				moduleFlavor: this.moduleFlavor,
				umcpCommand: this.umcpCommand,
				objectNamePlural: this.objectNamePlural,
				objectNameSingular: this.objectNameSingular,
				selectedContainer: this.selectedContainer,
				selectedSuperordinate: this.selectedSuperordinate
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
			this._preWizard.standbyDuring(all([this.createWizardAdded, wizardDeferred]));
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
							properties: detailsValues.properties
						});
						// insert at position 1. If another createWizard is added
						//   (after successfully saving the object) that
						//   wizard is also insert at 1, and removing this createWizard will
						//   selectChild(that_wizard), not firstPageWizard
						this._wizardContainer.addChild(createWizard, 1);
						this._wizardContainer.selectChild(createWizard);
						this.createWizardAdded.resolve();
						var finishWizard = lang.hitch(this, function(wizardFormValues, submit) {
							createWizard.standbyDuring(detailsValues.detailPage.loadedDeferred).then(lang.hitch(this, function() {
								lang.mixin(detailsValues.detailPage.templateObject._userChanges, createWizard.templateObject._userChanges);
								tools.forIn(wizardFormValues, lang.hitch(this, function(key, val) {
									detailsValues.detailPage._form.getWidget(key).set('value', val);
								}));
								createWizard.setCustomValues(wizardFormValues, detailsValues.detailPage._form);
								if (submit) {
									detailsValues.detailPage._form.ready().then(lang.hitch(this, function() {
										var saveDeferred = detailsValues.detailPage.save();
										if (saveDeferred.then) {
											createWizard.standbyDuring(saveDeferred);
											saveDeferred.then(
												lang.hitch(this, function() {
													this.addNotification(_('%s created', createWizard.objectName()));
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
