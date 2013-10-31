/*
 * Copyright 2011-2013 Univention GmbH
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
/*global define require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/topic",
	"dojo/promise/all",
	"dojo/Deferred",
	"dijit/Dialog",
	"dijit/layout/StackContainer",
	"umc/tools",
	"umc/modules/udm/cache",
	"umc/modules/udm/wizards/FirstPageWizard",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, on, topic, all, Deferred, Dialog, StackContainer, tools, cache, FirstPageWizard, _) {

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


			// depending on the list we get, create a form for adding
			// a new LDAP object
			var widgets = [];
			var layout = [];

			if ('navigation' != this.moduleFlavor) {
				// we need the container in any case
				widgets.push({
					type: 'ComboBox',
					name: 'container',
					label: _('Container'),
					description: _('The container in which the LDAP object shall be created.'),
					visible: containers.length > 1,
					staticValues: containers
				});
				layout.push('container');

				if (superordinates.length) {
					// we have superordinates
					widgets.push({
						type: 'ComboBox',
						name: 'superordinate',
						label: _('Superordinate'),
						description: _('The corresponding superordinate for the LDAP object.', this.objectNameSingular),
						staticValues: array.map(superordinates, function(superordinate) {
							return superordinate.title ? {id: superordinate.id, label: superordinate.title + ': ' + superordinate.label } : superordinate;
						}),
						visible: superordinates.length > 1,
						value: this.selectedSuperordinate
					}, {
						type: 'ComboBox',
						name: 'objectType',
						label: _('%s type', tools.capitalize(this.objectNameSingular)),
						value: this.defaultObjectType,
						description: _('The exact %s type.', this.objectNameSingular),
						umcpCommand: this.umcpCommand,
						dynamicValues: lang.hitch(this, function(options) {
							return this.moduleCache.getChildModules(options.superordinate, null, true);
						}),
						depends: 'superordinate'
					});
					layout.push('superordinate', 'objectType');
				} else {
					// no superordinates
					// object types
					if (types.length) {
						widgets.push({
							type: 'ComboBox',
							name: 'objectType',
							value: this.defaultObjectType,
							label: _('%s type', tools.capitalize(this.objectNameSingular)),
							description: _('The exact %s type.', this.objectNameSingular),
							visible: types.length > 1,
							staticValues: types
						});
						layout.push('objectType');
					}

					// templates
					if (templates.length) {
						templates.unshift({ id: 'None', label: _('None') });
						widgets.push({
							type: 'ComboBox',
							name: 'objectTemplate',
							value: this.defaultObjectType,  // see Bug #13073, for users/user, there exists only one object type
							label: _('%s template', tools.capitalize(this.objectNameSingular)),
							description: _('A template defines rules for default object properties.'),
							visible: templates.length > 1,
							staticValues: templates
						});
						layout.push('objectTemplate');
					}
				}
			} else {
				// for the navigation, we show all elements and let them query their content automatically
				widgets = [{
					type: 'HiddenInput',
					name: 'container',
					value: this.selectedContainer.id
				}, {
					type: 'Text',
					name: 'container_help',
					content: _('<p>The LDAP object will be created in the container:</p><p><i>%s</i></p>', this.selectedContainer.path || this.selectedContainer.label)
				}, {
					type: 'ComboBox',
					name: 'objectType',
					label: _('%s type', tools.capitalize(this.objectNameSingular)),
					description: _('The exact object type of the new LDAP object.'),
					visible: types.length > 1,
					staticValues: types
				}, {
					type: 'ComboBox',
					name: 'objectTemplate',
					label: _('%s template', tools.capitalize(this.objectNameSingular)),
					description: _('A template defines rules for default object properties.'),
					depends: 'objectType',
					umcpCommand: this.umcpCommand,
					dynamicValues: lang.hitch(this, function(options) {
						return this.moduleCache.getTemplates(options.objectType);
					}),
					staticValues: [ { id: 'None', label: _('None') } ]
				}];
				layout = [ 'container', 'container_help', 'objectType', 'objectTemplate' ];
			}

			this._wizardContainer = new StackContainer({
				style: 'width: 630px; height:310px;'
			});
			var firstPageWizard = new FirstPageWizard({
				pages: [{
					name: 'firstPage',
					headerText: this.get('title'),
					widgets: widgets,
					layout: layout
				}]
			});
			on.once(this, 'show', function() {
				if (!this.canContinue.isResolved()) {
					firstPageWizard.focusFirstWidget('firstPage');
				}
			});
			this._wizardContainer.addChild(firstPageWizard);
			this._wizardContainer.startup();
			this._wizardContainer.selectChild(firstPageWizard);
			this.own(this._wizardContainer);
			this.set('content', this._wizardContainer);

			firstPageWizard.on('Cancel', lang.hitch(this, function() {
				this.hide();
			}));
			firstPageWizard.on('Finished', lang.hitch(this, function() {
				var firstPageValues = firstPageWizard.getValues();
				firstPageValues.objectType = firstPageValues.objectType || this.moduleFlavor;
				var objectTypeName;
				array.some(types, function(type) {
					if (type.id == firstPageValues.objectType) {
						objectTypeName = type.label;
						return true;
					}
				});
				if (!objectTypeName) {
					// cache may return empty label for no sub modules
					objectTypeName = this.objectNameSingular;
				}
				this.mayCreateWizard.then(lang.hitch(this, function() {
					this.buildCreateWizard(firstPageWizard, firstPageValues, objectTypeName);
				}));
			}));

			var form = firstPageWizard._pages.firstPage._form;
			form.ready().then(lang.hitch(this, function() {
				var formNecessary = false;
				tools.forIn(form._widgets, function(iname, iwidget) {
					if (iwidget.getAllItems) { // ComboBox, but not HiddenInput
						var items = iwidget.getAllItems();
						if (items.length > 1) {
							formNecessary = true;
						}
					}
				});
				if (formNecessary) {
					this.canContinue.reject();
				} else {
					this.canContinue.resolve();
					firstPageWizard._finish();
				}
			}));
		},

		buildCreateWizard: function(firstPageWizard, firstPageValues, objectTypeName) {
			var moduleCache = cache.get(this.moduleFlavor);
			var wizardDeferred = moduleCache.getWizard(firstPageValues.objectType || this.moduleFlavor);
			if (this.wizardsDisabled) {
				wizardDeferred = new Deferred();
				wizardDeferred.reject();
			}
			this._readyForCreateWizard = new Deferred();
			firstPageWizard.standbyDuring(this.createWizardAdded);
			this.onFirstPageFinished(firstPageValues);

			wizardDeferred.then(
				lang.hitch(this, function(WizardClass) {
					this._readyForCreateWizard.then(lang.hitch(this, function(detailsValues) {
						var createWizard = new WizardClass({
							umcpCommand: this.umcpCommand,
							objectTypeName: objectTypeName,
							detailPage: detailsValues.detailPage,
							template: detailsValues.template,
							firstPageAvailable: this.canContinue.isRejected(),
							properties: detailsValues.properties
						});
						// insert at position 1. If another createWizard is added
						//   (after successfully saving the object) that
						//   wizard is also insert at 1, and removing this createWizard will
						//   selectChild(that_wizard), not firstPageWizard
						this._wizardContainer.addChild(createWizard, 1);
						this._wizardContainer.selectChild(createWizard);
						this.createWizardAdded.resolve();
						createWizard.focusFirstWidget('page0');
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
													this.buildCreateWizard(firstPageWizard, firstPageValues, objectTypeName);
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
							this._wizardContainer.selectChild(firstPageWizard);
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

