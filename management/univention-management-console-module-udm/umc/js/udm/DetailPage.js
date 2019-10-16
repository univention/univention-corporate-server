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
/*global require,define,setTimeout,window,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/Deferred",
	"dojo/promise/all",
	"dojo/when",
	"dojo/dom-construct",
	"dojo/dom-class",
	"dojo/topic",
	"dojo/json",
	"dojox/html/entities",
	"dijit/TitlePane",
	"umc/render",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/ContainerWidget",
	"umc/widgets/MultiInput",
	"umc/widgets/ComboBox",
	"umc/widgets/Form",
	"umc/widgets/Page",
	"umc/widgets/StandbyMixin",
	"umc/widgets/TabController",
	"dijit/layout/StackContainer",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/modules/udm/Template",
	"umc/modules/udm/OverwriteLabel",
	"umc/modules/udm/UMCPBundle",
	"umc/modules/udm/UsernameMaxLengthChecker",
	"umc/modules/udm/cache",
	"umc/i18n!umc/modules/udm",
	"dijit/registry",
	"umc/_all"
], function(declare, lang, array, on, Deferred, all, when, construct, domClass, topic, json, entities, TitlePane, render, tools, dialog, ContainerWidget, MultiInput, ComboBox, Form, Page, StandbyMixin, TabController, StackContainer, Text, Button, Template, OverwriteLabel, UMCPBundle, UsernameMaxLengthChecker, cache, _) {

	var Anchor = Text;
	require(['umc/widgets/Anchor'], function(A) {  // Anchor is new in UCS 4.4, so due to caching problems load it async
		Anchor = A;
	});
	var _StandbyPage = declare([Page, StandbyMixin], {});

	var FixedMultiInput = declare([MultiInput], {
		postMixInProperties: function() {
			this.inherited(arguments);
			this._resetValue = [];
			this.watch('max', lang.hitch(this, '_updateMax'));
		},

		setInitialValue: function(value) {
			this._resetValue = value;
			this.set('value', value);
		},

		_updateMax: function() {
			this._removeElement(this.get('value').length);
			this._updateNewEntryButton();
		}
	});

	return declare("umc.modules.udm.DetailPage", [ ContainerWidget, StandbyMixin ], {
		// summary:
		//		This class renderes a detail page containing subtabs and form elements
		//		in order to edit LDAP objects.

		// umcpCommand: Function
		//		Reference to the module specific umcpCommand function.
		umcpCommand: null,

		// moduleStore: Object
		//		Reference to module store of this module.
		moduleStore: null,

		// moduleFlavor: String
		//		Flavor of the module
		moduleFlavor: this.moduleFlavor,

		// operation: String
		// 		One of 'add', 'edit', 'copy'
		operation: null,

		// objectType: String
		//		The object type of the LDAP object that is edited.
		objectType: null,

		// ldapBase: String
		ldapBase: null,

		// ldapName: String?|String[]?
		//		The LDAP DN of the object that is edited. This property needs not to be set
		//		when a new object is edited. Can also be a list of LDAP DNs for multi-edit
		//		mode.
		ldapName: null,

		// newObjectOptions:
		// 		Dict containing options for creating a new LDAP object (chosen by the user
		// 		in the 'add object' dialog). This includes properties such as superordinate,
		//		the container in which the object is to be created, the object type etc.
		newObjectOptions: null,

		// isCloseable: Boolean?
		//		Specifies whether this
		isClosable: false,

		// note: String?
		//		If given, this string is displayed as note on the first page.
		note: null,

		// reference to the URI which is opened when clicking on the help button
		helpLink: null,

		// internal reference to the formular containing all form widgets of an LDAP object
		_form: null,

		// internal reference to the page containing the subtabs for object properties
		_tabs: null,

		// internal reference if Page is fully rendered
		_pageRenderedDeferred: null,

		// internal reference to a dict with entries of the form: policy-type -> widgets
		_policyWidgets: null,

		// Deferred object of the query and render process for the policy widgets
		_policyDeferred: null,

		// object properties as they are received from the server
		_receivedObjOrigData: null,

		// initial object properties as they are represented by the form
		_receivedObjFormData: null,

		// LDAP object type of the current edited object
		_editedObjType: null,

		// dict that saves which form element is displayed on which subtab
		// (used to display user input errors)
		_propertySubTabMap: null,

		// dict that saves the options that must be set for a property to be available
		_propertyOptionMap: null,

		// array that stores extra references to all sub tabs
		// (necessary to reset change sub tab titles [when displaying input errors])
		_detailPages: null,

		// reference to the policies tab
		_policiesTab: null,

		_multiEdit: false,

		_bundledCommands: null,

		// reference to the parent UMC module instance
		_parentModule: null,

		// reference to TabControllers of each subtab
		_tabControllers: null,

		isSyncedObject: null, // object which is modified (or one of multiedited) has univentionObjectFlag == synced

		standbyOpacity: 0,  // the standby animation should be transparent to improove visibility when loading the object

		postMixInProperties: function() {
			this.inherited(arguments);

			this._multiEdit = this.ldapName instanceof Array;
			this._tabControllers = [];
			this._pageRenderedDeferred = new Deferred();
			this.headerButtons = this.getButtonDefinitions();
		},

		buildRendering: function() {
			// summary:
			//		Query necessary information from the server for the object detail page
			//		and initiate the rendering process.
			this.inherited(arguments);

			domClass.add(this.domNode, 'umcUDMDetailPage');
			domClass.toggle(this.domNode, 'umcUDMUsersModule', this.moduleFlavor === 'users/user');

			// remember the objectType of the object we are going to edit
			this._editedObjType = this.objectType;

			// for the detail page, we first need to query property data from the server
			// for the layout of the selected object type, then we can render the page
			var objectDN = this._multiEdit || this.moduleFlavor == 'users/self' || this.ldapName instanceof Deferred ? null : this.ldapName || null;
			// prepare parallel queries
			var moduleCache = cache.get(this.moduleFlavor);
			this.propertyQuery = moduleCache.getProperties(this.objectType, objectDN);
			var commands = {
				properties: this.propertyQuery,
				layout: moduleCache.getLayout(this.objectType, objectDN),
				metaInfo: moduleCache.getMetaInfo(this.objectType)
			};
			if (!this._multiEdit) {
				// query policies for normal edit
				commands.policies = moduleCache.getPolicies(this.objectType);
			} else {
				// for multi-edit, mimic an empty list of policies
				commands.policies = new Deferred();
				commands.policies.resolve();
			}

			// in case an object template has been chosen, add the umcp request for the template
			var objTemplate = lang.getObject('objectTemplate', false, this.newObjectOptions);
			if (objTemplate && 'None' != objTemplate) {
				this.templateQuery = this.umcpCommand('udm/get', [objTemplate], true, 'settings/usertemplate');
				commands.template = this.templateQuery;
			} else {
				this.templateQuery = new Deferred();
				this.templateQuery.resolve(null);
			}

			// when the commands have been finished, create the detail page
			all(commands).then(lang.hitch(this, function(results) {
				var template = lang.getObject('template.result', false, results) || null;
				var layout = lang.clone(results.layout);
				var policies = lang.clone(results.policies);
				var properties = lang.clone(results.properties);
				setTimeout(lang.hitch(this, function() {
					render.requireWidgets(properties).then(lang.hitch(this, function() {
						this._prepareIndividualProperties(properties).then(lang.hitch(this, function(properties) {
							this.renderDetailPage(properties, layout, policies, template, results.metaInfo).then(lang.hitch(this, function() {
								this._pageRenderedDeferred.resolve();
							}), lang.hitch(this, function() {
								this._pageRenderedDeferred.reject();
							}));
						}));
					}));
				}), 50);
			}), lang.hitch(this, function() {
				this._pageRenderedDeferred.reject();
			}));
		},

		postCreate: function() {
			this.inherited(arguments);

			// standby handling
			this.watch('selected', lang.hitch(this, function() {
				var readyDeferred = this.ready();
				this.standbyDuring(readyDeferred);
				this._headerButtons.submit.set('disabled', true);
				readyDeferred.then(lang.hitch(this, function() {
					this._headerButtons.submit.set('disabled', false);
				}));
			}));
		},

		startup: function() {
			this.inherited(arguments);
			this._parentModule = tools.getParentModule(this);
		},

		_setHelpLinkAttr: function(helpLink) {
			this._set('helpLink', helpLink);
			domClass.toggle(this._headerButtons.help.domNode, 'dijitDisplayNone', !helpLink);
		},

		_loadObject: function(formBuiltDeferred, policyDeferred) {
			if (!this.ldapName || this._multiEdit) {
				// no DN given or multi edit mode
				return all({
					formBuild: formBuiltDeferred,
					properties: this.propertyQuery
				});
			}

			return all({
				object: this.getObject(this.ldapName),
				formBuilt: formBuiltDeferred
			}).then(lang.hitch(this, function(result) {
				// save the original data we received from the server
				var vals = result.object;
				this._receivedObjOrigData = vals;
				this._form.setFormValues(vals);
				this._getInitialFormValues();

				// as soon as the policy widgets are rendered, update the policy values
				policyDeferred.then(lang.hitch(this, function() {
					var policies = lang.getObject('_receivedObjOrigData.$policies$', false, this) || {};
					tools.forIn(policies, function(ipolicyType, ipolicyDNs) {
						// get the MultiInput to update its ComboBox value with the new DN
						if (ipolicyType in this._policyWidgets) {
							var iwidget = this._policyWidgets[ipolicyType].$policy$;
							if (ipolicyDNs.length > 1) {
								// by default we have a max constraint of 1 to disable that one can set multiple policies.
								// In case multiple policies are already set in the backend the user should be able to correctly modify them.
								iwidget.set('max', Infinity);
							}
							iwidget.setInitialValue(ipolicyDNs);
						}
					}, this);
				}));

				// show type and position of the object
				if (this.operation !== 'add') {
					var ldapName = this.ldapName;
					if (this.operation === 'copy') {
						ldapName = lang.replace('{0},{1}', [tools.explodeDn(this.ldapName)[0], this.newObjectOptions.container]);
					}
					var path = tools.ldapDn2Path(ldapName, this.ldapBase);
					var objecttype = _('Type: <i>%(type)s</i>', { type: vals.$labelObjectType$ });
					var position = _('Position: <i>%(path)s</i>', { path: path });
					var position_text = lang.replace('{0}<br>{1}', [objecttype, position]);
					array.forEach(this._tabs.getChildren(), lang.hitch(this, function(child) {
						if (child.position_text) {
							child.position_text.set('content', position_text);
						}
					}));
				}

				return this._form.ready();
			}));
		},

		getObject: function(dn) {
			if (this.operation === 'copy') {
				return this.umcpCommand('udm/copy', [dn], undefined, this.moduleFlavor).then(function(response) {
					return response.result[0];
				});
			}
			return this.moduleStore.get(dn);
		},

		ready: function() {
			return this._pageRenderedDeferred;
		},

		_getInitialFormValues: function() {
			this._receivedObjFormData = {
				$policies$: this._receivedObjOrigData.$policies$
			};
			tools.forIn(this._form._widgets, lang.hitch(this, function(iname, iwidget) {
				if (!(iname in this._receivedObjOrigData) && iwidget.isInstanceOf(ComboBox)) {
					// iname was not received from server and it is a ComboBox
					// => the value may very well be set because there is
					// no empty choice (in this case the first choice is selected).
					// this means that this value would not be
					// recognized as a change!
					// console.log(iname, ivalue); // uncomment this to see which values will be send to the server
					this._receivedObjFormData[iname] = '';
				} else if (iwidget.ready) {
					// get the initial value as soon as the widget is ready
					iwidget.ready().then(lang.hitch(this, function() {
						this._receivedObjFormData[iname] = iwidget.get('value');
					}));
				} else {
					// no ready method -> get initial value immediately
					this._receivedObjFormData[iname] = iwidget.get('value');
				}
			}));
		},

		_notifyAboutAutomaticChanges: function() {
			if (this.operation === 'add' || this.operation === 'copy' || this._multiEdit) {
				// ignore creation of a new object as well as the multi edit mode
				return;
			}
			// a direct call to haveValuesChanged() will yield true...
			// therefore we add a call to Form::ready()
			this._form.ready().then(lang.hitch(this, function() {
				var valuesChanged = this.hasEmptyPropsWithDefaultValues() || this.haveValuesChanged() || this.havePolicyReferencesChanged();
				if (valuesChanged) {
					var changes = [];
					var alteredValues = lang.mixin(this.getEmptyPropsWithDefaultValues(), this.getAlteredValues()); // order is important. overwrite default values from getEmptyPropsWithDefaultValues with altered values
					tools.forIn(alteredValues, lang.hitch(this, function(key, value) {
						if (key === '$dn$') {
							return;
						}
						if (this.shouldPreventPopupForEmptyPropWithDefault(key)) {
							return;
						}

						var widget = this._form.getWidget(key);
						if (widget && widget.get('visible')) {
							value = widget.get('value');
							if (value instanceof Array) {
								value = value.join(', ');
							}
							if (widget.isInstanceOf(ComboBox)) {
								array.forEach(widget.getAllItems(), function(item) {
									if (item.id == value) {
										value = item.label;
									}
								});
							}
							changes.push(lang.replace('<li>{tabName}{groupName} - {widgetName}: {value}</li>', {
								tabName: widget.$refTab$ ? widget.$refTab$.label: '',
								groupName: widget.$refTitlePane$ ? ' - ' + widget.$refTitlePane$.label: '',
								widgetName: widget.get('label') || key,
								value: value
							}));
						}
					}));
					if (changes.length) {
						changes = '\n<ul>' + changes.join('') + '</ul>';
						dialog.alert(_('The following empty properties were set to default values in the form. These values will be applied when saving.') + changes);
					}
				}
			}));
		},

		_renderPolicyTab: function(policies) {
			this._policyWidgets = {};
			if (policies && policies.length) {
				// in case we have policies that apply to the current object, we need an extra
				// sub tab that groups all policies together
				this._policiesTab = new _StandbyPage({
					title: _('Policies'),
					noFooter: true,
					headerText: _('Properties inherited from policies'),
					helpText: _('List of all object properties that are inherited by policies. The values cannot be edited directly. By clicking on "Create new policy", a new tab with a new policy will be opened. If an attribute is already set, the corresponding policy can be edited in a new tab by clicking on the "edit" link.')
				});
				this._addSubTab(this._policiesTab);
				this._policiesTab.watch('selected', lang.hitch(this, function(name, oldVal, newVal) {
					if (!newVal || this._policyDeferred.isFulfilled()) {
						return;
					}
					this._loadPolicies(policies).then(lang.hitch(this, function() {
						this._policyDeferred.resolve();
					}));
				}));
				if (this.operation === 'copy') {
					this._loadPolicies(policies).then(lang.hitch(this, function() {
						this._policyDeferred.resolve();
					}));
				}
			} else {
				// in case there are no policies, we use a dummy Deferred object
				this._policyDeferred.resolve();
			}
		},

		_loadPolicies: function(policies) {
			if (!policies || !policies.length) {
				return;
			}

			this._policiesTab.standby(true);

			var policiesContainer = new ContainerWidget({
			});
			this._policiesTab.addChild(policiesContainer);

			// sort policies by its label
			policies.sort(tools.cmpObjects({attribute: 'label'}));

			// we need to query for each policy object its properties and its layout
			// this can be done asynchronously
			var commands = [];
			array.forEach(policies, function(ipolicy) {
				var params = { objectType: ipolicy.objectType };
				commands.push(this.umcpCommandBundle('udm/properties', params));
				commands.push(this.umcpCommandBundle('udm/layout', params));
			}, this);

			// wait until we have results for all queries
			return all(commands).then(lang.hitch(this, function(results) {
				// parse the widget configurations
				array.forEach(results, lang.hitch(this, function(props, i, results) {
					if (i % 2) {
						return;
					}
					var ipolicy = policies[Math.floor(i / 2)];
					var ipolicyType = ipolicy.objectType;
					var iproperties = props.result;
					var ilayout = results[i + 1].result;
					var newLayout = [];

					// we only need to show the general properties of the policy... the "advanced"
					// properties would be rendered on the subtab "advanced settings" which we do
					// not need in this case
					array.forEach(ilayout, function(jlayout) {
						if (false === jlayout.advanced) {
							// we found the general properties of the policy
							newLayout = jlayout.layout;

							// break the loop
							return false;
						}
					});

					// build up a small map that indicates which policy properties will be shown
					// filter out the property 'name'
					var usedProperties = {};
					array.forEach(newLayout, function(jlayout) {
					   if (jlayout instanceof Array || typeof jlayout == "object") {
						   var nestedLayout = (undefined === jlayout.layout) ? jlayout : jlayout.layout;
							array.forEach(nestedLayout, function(klayout) {
								array.forEach(tools.stringOrArray(klayout), function(llayout) {
									if (typeof llayout == "string") {
										if ('name' != llayout) {
											usedProperties[llayout] = true;
										}
									}
								});
							});
						} else if (typeof jlayout == "string") {
							if ('name' != jlayout) {
								usedProperties[jlayout] = true;
							}
						}
					});

					// get only the properties that need to be rendered
					var newProperties = [];
					array.forEach(iproperties, function(jprop) {
						var jname = jprop.id || jprop.name;
						if (jname in usedProperties) {
							if (jprop.multivalue && 'MultiInput' != jprop.type) {
								// handle multivalue inputs
								jprop.subtypes = [{
									type: jprop.type,
									dynamicValues: jprop.dynamicValues,
									dynamicValuesInfo: jprop.dynamicValuesInfo,
									dynamicOptions: jprop.dynamicOptions,
									staticValues: jprop.staticValues,
									size: jprop.size,
									depends: jprop.depends
								}];
								jprop.type = 'MultiInput';
							}
							jprop.disabled = true; // policies cannot be edited

							// store the original label (we will modify it)
							jprop.$orgLabel$ = jprop.label;
							if (jprop.subtypes instanceof Array) {
								// in case we have subtypes (e.g. for MultiInput),
								// prefer their labels over the widget's one
								jprop.$orgLabel$ = [];
								array.forEach(jprop.subtypes, function(itype, i) {
									// set the subtype label
									var subTypeLabel = itype.label || (i === 0 && jprop.label ? jprop.label : '&nbsp;');
									jprop.$orgLabel$.push(subTypeLabel);
								});
							}

							// add an empty label to ComboBox so that _firstValueInList
							//   is an empty string. This will empty the choice of
							//   this widget in case there is no value set (instead of the first)
							//   see Bug #31017
							if (jprop.type.indexOf('ComboBox') >= 0) {
								if (jprop.staticValues) {
									jprop.staticValues = lang.clone(jprop.staticValues);
									jprop.staticValues.unshift({id: '', label: ''});
								} else {
									jprop.staticValues = [{id: '', label: ''}];
								}
							}
							newProperties.push(jprop);
						}
					}, this);

					// make sure that the widget use the flavored umcpCommand
					array.forEach(newProperties, function(iprop) {
						iprop.umcpCommand = this.umcpCommand;
					}, this);

					// for the policy group, we need a ComboBox that allows to link an object
					// to a particular policy
					newProperties.push({
						type: FixedMultiInput,
						max: 1,
						name: '$policy$',
						label: _('Select policy configuration'),
						description: _('Select policies that should be directly linked to the current LDAP object'),
						onChange: lang.hitch(this, '_updatePolicy', ipolicyType),
						subtypes: [{
							type: ComboBox,
							dynamicValues: lang.hitch(this, '_queryPolicies', ipolicyType),
							onChange: lang.hitch(this, function(dn, widgets) {
								tools.forIn(widgets, lang.hitch(this, function(key, widget) {
									if (widget.isPolicyEdit) {
										widget.set('label', '');
										widget.set('disabled', !dn);
									}
								}));
							})
						}, {
							type: Button,
							name: 'edit',
							isPolicyEdit: true,
							iconClass: 'umcIconEdit',
							disabled: true,
							description: _('Edit policy'),
							'class': 'umcUDMMultiInputEditButton umcOutlinedButton umcIconButton--aligned-to-textfield',
							callback: lang.hitch(this, function(dn) {
								this._openPolicy(ipolicyType, dn);
							})
						}]
					});
					var buttonsConf = [{
						type: Button,
						name: '$addPolicy$',
						'class': 'umcMultiInputAddButton umcOutlinedButton', // use umcMultiInputAddButton since this button needs same styling
						label: _('Create new policy'),
						callback: lang.hitch(this, '_openPolicy', ipolicyType, undefined)
					}];
					newLayout.unshift(['$policy$']);

					// render the group of properties
					var widgets = render.widgets(newProperties, this);
					this._policyWidgets[ipolicyType] = widgets;
					var buttons = render.buttons(buttonsConf, this);
					widgets.$policy$.addChild(buttons.$addPolicy$);
					policiesContainer.addChild(new TitlePane({
						title: ipolicy.label,
						description: ipolicy.description,
						open: false,
						content: render.layout(newLayout, widgets)
					}));
				}));

				this._policiesTab.standby(false);
			}));
		},

		_prepareWidgets: function(_properties) {
			// parse the widget configurations
			var properties = [];
			var optionMap = {};
			array.forEach(_properties, function(iprop) {
				// ignore internal properties
				if (iprop.id.slice(0, 1) == '$' && iprop.id.slice(-1) == '$') {
					properties.push(iprop);
					return;
				}

				if (iprop.syntax === 'PortalCategorySelection') {
					iprop.dndOptions = {
						type: ['PortalCategorySelection'],
						accept: ['PortalCategory']
					};
					iprop.subtypes[1].dndOptions = {
						type: ['PortalEntrySelection'],
						accept: ['PortalEntry']
					};
				}

				// handle size classes for MultiInputs that are defined at the
				// object property and that overwrite the syntax default
				if (iprop.size instanceof Array && iprop.subtypes instanceof Array && iprop.size.length == iprop.subtypes.length) {
					array.forEach(iprop.size, function(isize, idx) {
						iprop.subtypes[idx].size = isize;
					});
				}

				// handle editable items
				if (iprop.readonly) {
					iprop.disabled = true;
				} else {
					if (iprop.disabled !== true) {
						iprop.disabled = this.operation === 'add' ? false : ! iprop.editable;
					}
				}
				if (this._multiEdit && iprop.identifies) {
					// in multi-edit mode, one cannot edit the 'name' field, i.e., the identifier
					iprop.disabled = true;
				}

				properties.push(iprop);
				optionMap[ iprop.id ] = iprop.options;
			}, this);
			this._propertyOptionMap = optionMap;

			// special case for password, it is only required when a new user is added
			if (!this.newObjectOptions) {
				array.forEach(properties, function(iprop) {
					if ('password' == iprop.id) {
						iprop.required = false;
						return false;
					}
				});
			}

			// make sure that the widget use the flavored umcpCommand
			array.forEach(properties, function(iprop) {
				iprop.umcpCommand = this.umcpCommand;
			}, this);

			return properties;
		},

		_prepareAdvancedSettings: function(_layout) {
			// parse the layout configuration... we would like to group all groups of advanced
			// settings on a special sub tab
			var advancedGroup = {
				label: _('Advanced settings'),
				description: _('Advanced settings'),
				layout: []
			};
			var layout = [];
			array.forEach(_layout, function(ilayout) {
				if (ilayout.advanced) {
					// advanced groups of settings should go into one single sub tab
					var jlayout = lang.mixin({ open: false }, ilayout);
					advancedGroup.layout.push(jlayout);
				} else {
					layout.push(ilayout);
				}
			});

			// if there are advanced settings, add them to the layout
			if (advancedGroup.layout.length) {
				layout.push(advancedGroup);
			}
			return layout;
		},

		active_directory_enabled: function() {
			var ucr = lang.getObject('umc.modules.udm.ucr', false) || {};
			return tools.isTrue(ucr['ad/member']);
		},

		_prepareIndividualProperties: function(properties) {
			var deferred = new Deferred();
			var activeDirectoryEnabled = this.active_directory_enabled();
			if (!activeDirectoryEnabled) {
				deferred.resolve(properties);
				return deferred;
			}

			var _isSyncedObject = function(obj) {
				return obj.$flags$.length && obj.$flags$[0].indexOf('synced') >= 0;
			};

			// the following checks are only necessary for the AD member mode
			when(this.ldapName, lang.hitch(this, function(ldapName){
				this.ldapName = ldapName;
				if (!ldapName || this.operation === 'copy') {
					// new object / multiEdit / copy...
					deferred.resolve(properties);
					return;
				}

				var objects = ldapName;
				if (!this._multiEdit) {
					objects = [objects];
				}
				// load all objects to see if they have univentionObjectFlag == synced
				all(array.map(objects, lang.hitch(this, function(dn) {
					return this.moduleStore.get(dn);
				}))).then(lang.hitch(this, function(objs) {
					if (array.some(objs, _isSyncedObject)) {
						properties = this._disableSyncedReadonlyProperties(properties);
						this.isSyncedObject = true;
					}
					deferred.resolve(properties);
				}), function() { deferred.resolve(properties); });
			}));
			return deferred;
		},

		_disableSyncedReadonlyProperties: function(properties) {
			array.forEach(properties, lang.hitch(this, function(prop) {
				if (prop.readonly_when_synced) {
					prop.disabled = true;
				}
			}));
			return properties;
		},

		addActiveDirectoryWarning: function() {
			var _nameText = lang.hitch(this, function(n, value) {
				var text = {
					'users/user'          : _.ngettext('The user "%s" is part of the Active Directory domain.',
					                                    'The users are part of the Active Directory domain.', n, value),
					'groups/group'        : _.ngettext('The group "%s" is part of the Active Directory domain.',
					                                    'The groups are part of the Active Directory domain.', n, value),
					'computers/computer'  : _.ngettext('The computer "%s" is part of the Active Directory domain.',
					                                    'The computers are part of the Active Directory domain.', n, value),
					'networks/network'    : _.ngettext('The network object "%s" is part of the Active Directory domain.',
					                                    'The network objects are part of the Active Directory domain.', n, value),
					'dns/dns'             : _.ngettext('The DNS object "%s" is part of the Active Directory domain.',
					                                    'The DNS objects are part of the Active Directory domain.', n, value),
					'dhcp/dhcp'           : _.ngettext('The DHCP object "%s" is part of the Active Directory domain.',
					                                    'The DHCP objects are part of the Active Directory domain.', n, value),
					'shares/share'        : _.ngettext('The share "%s" is part of the Active Directory domain.',
					                                    'The shares are part of the Active Directory domain.', n, value),
					'shares/print'        : _.ngettext('The printer "%s" is part of the Active Directory domain.',
					                                    'The printers are part of the Active Directory domain.', n, value),
					'mail/mail'           : _.ngettext('The mail object "%s" is part of the Active Directory domain.',
					                                    'The mail objects are part of the Active Directory domain.', n, value),
					'nagios/nagios'       : _.ngettext('The Nagios object "%s" is part of the Active Directory domain.',
					                                    'The Nagios objects are part of the Active Directory domain.', n, value),
					'policies/policy'     : _.ngettext('The policy "%s" is part of the Active Directory domain.',
					                                    'The policies are part of the Active Directory domain.', n, value),
					'settings/portal_all' : _.ngettext('The portal object "%s" is part of the Active Directory domain.',
					                                    'The portal objects are part of the Active Directory domain.', n, value)
				}[this.moduleFlavor];
				if (!text) {
					text = _.ngettext('The LDAP object "%s" is part of the Active Directory domain.',
					                   'The LDAP objects are part of the Active Directory domain.', n, value );
				}
				text = _('<b>Attention:</b> ') + text + _(' UCS can only change certain attributes.');
				return text;
			});

			if (!this.active_directory_enabled() || this.operation === 'add' || !this.isSyncedObject) {
				return;
			}
			var value = '';
			var name;
			// for multi edit, this.ldapName is an array
			var editCount = this._multiEdit ? this.ldapName.length : 1;
			if (!this._multiEdit) {
				tools.forIn(this._form._widgets, function(name, widget) {
					if (widget.identifies) {
						value = widget.get('value');
						value = value instanceof Array ? value.join(" ") : value;
						return false; // break out of forIn
					}
				}, this);
			}
			name = _nameText(editCount, value);

			if (!this.adInformation) {
				this.adInformation = new Text({
					content: name,
					'class': 'umcUDMDetailPageWarning'
				});
				this.own(this.adInformation);

				var page = this._tabs.getChildren()[0];
				page.addChild(this.adInformation, 0);
			}
		},

		_prepareOptions: function(properties, layout, template, formBuiltDeferred) {
			var isNewObject = this.operation === 'add';

			var _getOptionProperty = function(properties) {
				var result = array.filter(properties, function(item) {
					return item.id === '$options$';
				});
				return result.length ? result[0] : null;
			};

			var option_prop = _getOptionProperty(properties);
			option_prop.labelConf = {'style': 'display: block;'};
			if (!option_prop || !option_prop.widgets.length) {
				properties = array.filter(properties, function(item) {
					return item.id !== '$options$';
				});
				return properties;
			}

			var option_values = {};
			var option_widgets = [];
			var option_layout = [];
			var app_layout = [];
			array.forEach(option_prop.widgets, function(option) {
				option = lang.clone(option);
				// special case: bring options from template into the widget
				if (template && template._options) {
					option.value = template._options.indexOf(option.id) > -1;
				}
				if (option.is_app_option) {
					option.labelConf = {
						'class': 'udmAppLabel'
					};
				}
				option_widgets.push(lang.mixin({
					disabled: isNewObject ? false : ! option.editable,
					size: option.is_app_option ? 'One' : 'Two'
				}, option));
				option_values[option.id] = option.value;

				if (option.is_app_option) {
					if (app_layout.length && app_layout[app_layout.length - 1].length === 1) {
						app_layout[app_layout.length - 1].push(option.id);
					} else {
						app_layout.push([option.id]);
					}
				} else {
					option_layout.push(option.id);
				}
			});

			var optiontab = {
				label: _('Options'),
				description: _('Options describing the basic features of the LDAP object'),
				layout: [ '$options$' ]
			};

			option_prop.widgets = option_widgets;
			option_prop.layout = [];
			if (app_layout.length) {
				option_prop.layout.push({
					label: _('Activated Apps'),
					toggleable: false,
					layout: app_layout,
					description: _('Here you can activate the user for one of the installed apps. The user can then log on to the app and use it.'),
				});
				optiontab = {
					label: _('Apps'),
					description: _('Activate apps and options'),
					layout: [ '$options$' ]
				};
			}
			if (option_layout.length) {
				option_prop.layout.push({
					label: _('Options'),
					toggleable: false,
					layout: option_layout
				});
			}

			// replace the existing tab (which exists so that it's displayed earlier)
			var tab = array.filter(layout, function(item) { return item.label === 'Apps'; });
			if (!tab.length) {
				layout.push(optiontab);
			} else {
				optiontab.layout = optiontab.layout.concat(tab[0].layout);
				lang.mixin(tab[0], optiontab);
			}

			formBuiltDeferred.then(lang.hitch(this, function() {
				var hasOptions = '$options$' in this._form.widgets;
				if (!hasOptions || this._multiEdit || !isNewObject) {
					return;
				}

				// set options... required when creating a new object
				var optionsWidget = this._form.widgets.$options$;
				optionsWidget.set('value', option_values);
			}));

			return properties;
		},

		_registerOptionWatchHandler: function() {
			// connect to onChange for the options property if it exists
			var optionsWidget = this._form.widgets.$options$;
			if (!optionsWidget) {
				return;
			}
			this.own(optionsWidget.watch('value', lang.hitch(this, function(attr, oldVal, newVal) {
				this.onOptionsChanged(newVal);
			})));
		},

		_autoUpdateTabTitle: function(widgets) {
			if (this._multiEdit) {
				this.moduleWidget.set('title', this.moduleWidget.defaultTitle + ' ' + _('(multi-edit)'));
			} else {
				// find property identifying the object
				tools.forIn(widgets, function(name, widget) {
					if (widget.identifies) {
						// watch value and modify title (escaped)
						this.own(widget.watch('value', lang.hitch(this, function(attr, oldValue, _value) {
							var value = _value instanceof Array ? _value.join(" ") : _value;
							this.moduleWidget.set('titleDetail', value);
						})));
						return false; // break out of forIn
					}
				}, this);
			}
		},

		_renderSubTabs: function(widgets, layout, metaInfo) {
			// render the layout for each subtab
			this._propertySubTabMap = {}; // map to remember which form element is displayed on which subtab
			this._detailPages = [];

			return tools.forEachAsync(layout, function(ilayout, idx) {
				// create a new page, i.e., subtab
				var subTab = new Page({
					title: entities.encode(ilayout.label || ilayout.name).replace(/ /g, '&nbsp;'), //TODO: 'name' should not be necessary
					titleAllowHTML: true,
					noFooter: true,
					headerText: ilayout.description || ilayout.label || ilayout.name,
					helpText: ilayout.help_text || (idx === 0 && metaInfo.help_text ? metaInfo.help_text : ''),
					helpTextAllowHTML: true
				});

				// add user photo into 'nav' area and adjust some properties
				var hasPhotoInLayout = array.some(ilayout.layout, function(l) {
					var hasPhoto = array.indexOf(l.layout, 'jpegPhoto') !== -1;
					if (hasPhoto) {
						l.layout.pop('jpegPhoto');
					}
					return hasPhoto;
				});
				if (widgets.jpegPhoto && hasPhotoInLayout) {
					lang.mixin(widgets.jpegPhoto, {
						region: 'nav',
						maxSize: 262144, // make sure that user pictures are not too large
						imageType: 'jpeg' // type must be jpeg to match the LDAP type specification
					});
					subTab.addChild(widgets.jpegPhoto);
				}

				// add rendered layout to subtab and register subtab
				render.layout(ilayout.layout, widgets, undefined, undefined, subTab);
				ilayout.$refSubTab$ = subTab;
				this._addSubTab(subTab);

				// update _propertySubTabMap
				this._detailPages.push(subTab);
				var layoutStack = [ ilayout.layout ];
				while (layoutStack.length) {
					var ielement = layoutStack.pop();
					if (ielement instanceof Array) {
						layoutStack = layoutStack.concat(ielement);
					} else if (typeof ielement == "string") {
						this._propertySubTabMap[ielement] = subTab;
					} else if (ielement.layout) {
						layoutStack.push(ielement.layout);
					}
				}
			}, this, 1, 20).then(lang.hitch(this, function() {
				this._layoutMap = layout;
			}));
		},

		_indentAppTabs: function(properties) {
			var _getOptionProperty = function(properties) {
				var result = array.filter(properties, function(item) {
					return item.id === '$options$';
				});
				return result.length ? result[0] : {widgets: []};
			};
			var appOptions = array.map(array.filter(_getOptionProperty(properties).widgets, function(option) { return option.is_app_option; }), function(option) { return option.id; });
			array.forEach(properties, function(prop) {
				array.forEach(prop.options, lang.hitch(this, function(option) {
					if (~array.indexOf(appOptions, option)) {
						var orgTitle = this._propertySubTabMap[prop.id].get('title');
						if (orgTitle.indexOf('<') !== 0) {
							this._propertySubTabMap[prop.id].set('title', '<span class="appTabIndented">' + orgTitle + '</span>');
						}
					}
				}));
			}, this);

			this._appOptionTabsMap = {};
			array.forEach(appOptions, lang.hitch(this, function(option) {
				tools.forIn(this._propertyOptionMap, lang.hitch(this, function(prop, options) {
					if (array.indexOf(options, option) !== -1 && prop in this._propertySubTabMap) {
						this._appOptionTabsMap[option] = this._propertySubTabMap[prop];
						this._appOptionTabsMap[option].is_app_tab = true;
						return false;
					}
				}));
			}));
		},

		_addReferencesToWidgets: function() {
			var _walk = lang.hitch(this, function(something, group, page) {
				if (typeof something == 'string') {
					var widget = this._form.getWidget(something);
					if (widget) {
						widget.$refTitlePane$ = group;
						widget.$refTab$ = page;
					}
				} else if (something instanceof Array) {
					array.forEach(something, function(something2) {
						_walk(something2, group, page);
					});
				} else if (typeof something == 'object') {
					_walk(something.layout, group, page);
				}
			});
			array.forEach(this._layoutMap, function(page) {
				array.forEach(page.layout, function(group) {
					if (group instanceof Array) {
						_walk(group, undefined, page);
						return;
					}
					array.forEach(group.layout, function(something) {
						_walk(something, group, page);
					});
				});
			});
		},

		_setTabVisibility: function(page, visible) {
			//if (page.is_app_tab) {
			//	page.set('disabled', !visible);
			//	return;
			//}
			array.forEach(this._tabControllers, lang.hitch(this, function(itabController) {
				itabController.setVisibilityOfChild(page, visible);
			}));
		},

		_addSubTab: function(page) {
			var tabController = new TabController({
				region: 'nav',
				containerId: this._tabs.id,
				nested: true
			});
			this._tabControllers.push(tabController);
			page.position_text = new Text({'class': 'positionText', region: 'nav', content: ''});

			page.addChild(tabController, 0);
			page.own(tabController);

			page.addChild(page.position_text);
			page.own(page.position_text);

			this._tabs.addChild(page);
			this.own(page);
		},

		_renderAppTabIcons: function(widgets) {
			if (!widgets.hasOwnProperty('$options$')) {
				return;
			}

			var appWidgets = tools.values(widgets.$options$._widgets).filter(function(w) {
				return w.is_app_option;
			});

			appWidgets.forEach(function(w) {
				construct.create('div', {
					'class': 'udmAppIcon ' + tools.getIconClass(w.icon, 'scalable')
				}, w.$refLabel$.domNode);
			});
		},

		_renderMultiEditCheckBoxes: function(widgets) {
			if (!this._multiEdit) {
				return;
			}

			var addCheckbox = lang.hitch(this, function(iwidget) {
				if (iwidget.$refLabel$ && !iwidget.disabled) {
					iwidget.$refLabel$.set('style', 'flex-wrap: wrap;');
					iwidget.$refOverwrite$ = this.own(new OverwriteLabel({}))[0];
					construct.place(iwidget.$refOverwrite$.domNode, iwidget.$refLabel$.domNode);
				}
			});

			// in multi-edit mode, hook a 'overwrite?' checkbox after each widget
			tools.forIn(widgets, function(iname, iwidget) {
				if (iname === '$options$') {
					tools.values(iwidget._widgets).forEach(function(iiwidget) {
						addCheckbox(iiwidget);
					});
				} else {
					addCheckbox(iwidget);
				}
			});
		},

		_renderForm: function(widgets) {
			// setup detail page, needs to be wrapped by a form (for managing the
			// form entries)
			var container = new ContainerWidget({});
			container.addChild(this._tabs);
			this.own(container);

			// create the form containing the whole Container as content and add
			// the form as content of this class
			this._form = new Form({
				'class': 'umcUDMDetailForm',
				widgets: widgets,
				content: container,
				moduleStore: this.moduleStore,
				onSubmit: lang.hitch(this, 'save'),
				style: 'margin: 0'
			});
			this.own(this._form);
			this._addReferencesToWidgets();

			this.addChild(this._form);

			this._form._buttons = render.buttons(this._form.buttons || [], this);
			array.forEach(this._form._buttons.$order$, function(ibutton) {
				container.addChild(ibutton);
			});
		},

		renderDetailPage: function(properties, layout, policies, template, metaInfo) {
			// summary:
			//		Render the form with subtabs containing all object properties that can
			//		be edited by the user.

			this._formBuiltDeferred = new Deferred();
			this._policyDeferred = new Deferred();
			var loadedDeferred = when(this.ldapName, lang.hitch(this, function(ldapName) {
				this.ldapName = ldapName;
				return this._loadObject(this._formBuiltDeferred, this._policyDeferred);
			}));
			loadedDeferred.then(lang.hitch(this, 'addActiveDirectoryWarning'));
			loadedDeferred.then(lang.hitch(this, 'set', 'helpLink', metaInfo.help_link));
			all([loadedDeferred, this._formBuiltDeferred]).then(lang.hitch(this, '_notifyAboutAutomaticChanges'));
			all([loadedDeferred, this._formBuiltDeferred]).then(lang.hitch(this, function() {
				// In multi-edit, onOptionsChanged() does not trigger when opening the detailpage
				// since no form values are getting set. So call it once manually.
				if (this._multiEdit) {
					this.onOptionsChanged();
				}
			}));

			if (template && template.length > 0) {
				template = template[0];
			} else {
				template = null;
			}
			// create detail page
			this._tabs = new StackContainer({
				region: 'main'
			});

			// prepare widgets and layout
			properties = this._prepareWidgets(properties);
			layout = this._prepareAdvancedSettings(layout);
			properties = this._prepareOptions(properties, layout, template, this._formBuiltDeferred);

			// render widgets and full layout
			var widgets = render.widgets(properties, this);
			if (this.moduleFlavor === 'users/user' && widgets.username) {
				this.usernameMaxLengthChecker = new UsernameMaxLengthChecker({textBoxWidget: widgets.username});
			}
			this._autoUpdateTabTitle(widgets);
			this._renderSubTabs(widgets, layout, metaInfo).then(lang.hitch(this, function() {
				this._indentAppTabs(properties);
				this._renderPolicyTab(policies);
				this._renderForm(widgets);
				this._renderAppTabIcons(widgets);
				this._renderMultiEditCheckBoxes(widgets);
				this._registerOptionWatchHandler();
				this._formBuiltDeferred.resolve();
				// this._addFurtherSettingsToApps();

				// initiate the template mechanism (only for new objects)
				// searches for given default values in the properties... these will be replaced
				this.templateObject = this.buildTemplate(template, properties, widgets);

				if (this.note) {
					// display notes
					this.addNotification(this.note);
				}
			}));
			//this._tabs.selectChild(this._tabs.getChildren[0]);

			return all([loadedDeferred, this._formBuiltDeferred]);
		},

		_addFurtherSettingsToApps: function() {
			tools.forIn(this._appOptionTabsMap, lang.hitch(this, function(option, tab) {
				this._form._widgets.$options$._widgets[option].$refLabel$.labelNodeRight.parentElement.appendChild(new Anchor({
					content: _('Further settings'),
					callback: lang.hitch(this, function(evt) {
						evt.preventDefault();
						this._form._widgets.$options$._widgets[option].set('value', true);
						this._tabs.selectChild(tab);
					}),
					style: 'display: inline; padding-left: 2em;'
				}).domNode);
			}));
		},

		buildTemplate: function(_template, properties, widgets) {
			if (this.operation === 'edit') {
				return;
			}

			// search for given default values in the properties... these will be replaced
			// by the template mechanism
			var template = {};
			array.forEach(properties, function(iprop) {
				if (iprop['default']) {
					var defVal = iprop['default'];
					if (typeof defVal == "string" && iprop.multivalue) {
						defVal = [ defVal ];
					}
					template[iprop.id] = defVal;
				}
			});

			// mixin the values set in the template object (if given)
			if (_template) {
				tools.forIn(_template, lang.hitch(this, function(key, value) {
					// $dn$, $options$, etc of the template
					// should not be values for the object
					if ((/^\$.*\$$/).test(key)) {
						delete _template[key];
					}
					if ((/^_.+$/).test(key)) {
						var specialWidget = this[key + 'Widget'];
						// TODO: it may be important to solve this generically
						// by now, only _options will go this path
						// and optionsWidget needs a special format
						var specialValue = {};
						array.forEach(value, function(val) {
							specialValue[val] = true;
						});
						if (specialWidget) {
							specialWidget.set('value', specialValue);
						}
						delete _template[key];
					}
				}));
				template = lang.mixin(template, _template);
			}

			// create a new template object that takes care of updating the elements in the form
			return new Template({
				widgets: widgets,
				template: template,
				operation: this.operation
			});
		},

		getButtonDefinitions: function() {
			var _createLabelText = lang.hitch(this, function() {
				var text = {
					'users/user'        : _('Create user'),
					'groups/group'      : _('Create group'),
					'computers/computer': _('Create computer'),
					'networks/network'  : _('Create network object'),
					'dns/dns'           : _('Create DNS object'),
					'dhcp/dhcp'         : _('Create DHCP object'),
					'shares/share'      : _('Create share'),
					'shares/print'      : _('Create printer'),
					'mail/mail'         : _('Create mail object'),
					'nagios/nagios'     : _('Create Nagios object'),
					'policies/policy'   : _('Create policy')
				}[this.moduleFlavor];
				if (!text && this.moduleFlavor === 'settings/portal_all') {
					text = {
						'settings/portal'          : _('Create portal'),
						'settings/portal_entry'    : _('Create portal entry'),
						'settings/portal_category' : _('Create portal category')
					}[this.objectType];
				}
				if (!text) {
					text = _('Create LDAP object');
				}
				return text;
			});

			var createLabel = '';
			if (this.operation === 'add' || this.operation === 'copy') {
				createLabel = _createLabelText();
			} else {
				createLabel = _('Save');
			}
			var closeLabel = _('Back');
			if (this.isClosable) {
				closeLabel = _('Cancel');
			}

			var buttonDefinitions = [
			{
				name: 'submit',
				iconClass: 'umcSaveIconWhite',
				label: createLabel,
				callback: lang.hitch(this, function() {
					this._form.onSubmit();
				})
			}, {
				name: 'help',
				iconClass: 'umcHelpIconWhite',
				label: _('Help'),
				'class': 'dijitDisplayNone',
				callback: lang.hitch(this, function() {
					window.open(this.helpLink);
				})
			}, {
				name: 'close',
				label: closeLabel,
				iconClass: 'umcCloseIconWhite',
				callback: lang.hitch(this, 'confirmClose')
			}];

			var extendableModules = [
				'users/user',
				'groups/group',
				'computers/computer'
			];
			if (array.indexOf(extendableModules, this.moduleFlavor) >= 0) {
				buttonDefinitions.unshift({
					name: 'extendedAttr',
					iconClass: 'umcExtendedAttrIconWhite',
					label: _('Customize this page'),
					callback: lang.hitch(this, function() {
						var version = tools.status('ucsVersion').split('-')[0];
						var link = _('https://docs.software-univention.de/manual-%s.html#central:extendedattrs', version);
						window.open(link);
					})
				});
			}

			return buttonDefinitions;
		},

		getValues: function() {
			// get all form values
			var vals = this._form.get('value');

			// get also policy values... can not be handled as standard form entry
			// explicitly exclude users/self. FIXME: find a way
			// to receive some udm-module-configuration for that
			var policiesLoaded = this._policyDeferred.isFulfilled();
			var isUsersSelf = this.objectType == 'users/self';
			if (!isUsersSelf && policiesLoaded) {
				vals.$policies$ = {};
				tools.forIn(this._policyWidgets, function(ipolicyType, iwidgets) {
					var ival = iwidgets.$policy$.get('value');
					if (ival.length) {
						vals.$policies$[ipolicyType] = ival;
					}
				}, this);
			}

			return vals;
		},

		_queryPolicies: function(objectType) {
			return this.umcpCommand('udm/query', {
				objectType: objectType,
				container: 'all',
				objectProperty: 'None',
				objectPropertyValue: ''
			}).then(function(data) {
				return array.map(data.result, function(ientry) {
					return ientry.$dn$;
				});
			});
		},

		// TODO: this could very well go into tools.
		// for now, it is only tested to work with udm/object/policies
		umcpCommandBundle: function(command, params) {
			if (!this._bundledCommands) {
				this._bundledCommands = {};
			}
			if (this._bundledCommands[command] === undefined) {
				this._bundledCommands[command] = new UMCPBundle(command, this.umcpCommand);
			}
			var bundle = this._bundledCommands[command];
			var deferred = bundle.addParams(params);
			return deferred;
		},

		_updatePolicy: function(policyType, policyDNs) {
			// make sure the given policyType exists
			if (!(policyType in this._policyWidgets)) {
				return;
			}

			// evaluate the policy with the given policyType and policy DNs
			this.umcpCommandBundle('udm/object/policies', {
				objectType: this.objectType,
				policies: policyDNs,
				policyType: policyType,
				objectDN: this.ldapName || null,
				container: this.newObjectOptions ? this.newObjectOptions.container : null
			}).then(lang.hitch(this, function(data) {
				tools.forIn(this._policyWidgets[policyType], function(iname, iwidget) {

					if (iname == '$policy$') {
						return;
					}

					var _editLabelFunc = lang.hitch(this, function(label, dn) {
						return lang.replace('{label} (<a href="javascript:void(0)" ' +
								'onclick=\'require("dijit/registry").byId("{id}")._openPolicy("{type}", "{dn}")\' ' +
								'title="{title}: {dn}">{edit}</a>)', {
							label: label,
							id: this.id,
							type: policyType,
							dn: dn,
							title: _('Click to edit the inherited properties of the policy'),
							edit: _('edit')
						});
					});

					var _undefinedLabelFunc = function(label) {
						return lang.replace('{label} (<span class="umcUnsetPolicy">{edit}</span>)', {
							label: label,
							edit: _('not defined')
						});
					};

					var _getLabel = function(labelFunc, dn) {
						var label = '';
						if (iwidget.$orgLabel$ instanceof Array) {
							label = array.map(iwidget.$orgLabel$, function(ilabel, i) {
								// only add the edit link to the first entry
								return i === 0 ? labelFunc(ilabel, dn) : ilabel;
							});
						}
						else {
							label = labelFunc(iwidget.$orgLabel$, dn);
						}
						return label;
					};

					// set the value and label
					var iinfo = data.result[iname];
					if (!iinfo) {
						// no policy values are inherited
						iwidget.set('value', ''); // also sets CheckBox to false
						iwidget.set('label', _getLabel(_undefinedLabelFunc));
					} else if (!(iinfo instanceof Array)) {
						// standard policy
						iwidget.set('value', iinfo.value);
						iwidget.set('label', _getLabel(_editLabelFunc, iinfo.policy));
					} else if (iinfo instanceof Array && iwidget.isInstanceOf(MultiInput)) {
						// we got probably a UCR-Policy, this is a special case:
						// -> a list of values where each value might have been inherited
						//    by different policies
						// FIXME: THIS IS NOT TRUE!
						//   UCC desktop policy also goes this way. Did not search further
						iwidget.set('value', array.map(iinfo, function(ival) {
							return ival.value;
						}));

						iwidget.ready().then(lang.hitch(this, function() {
							var labels = array.map(iinfo, function(jinfo, j) {
								if (iwidget._rowContainers.length < j) {
									// default to the original label
									return iwidget.$orgLabel$;
								}
								return _getLabel(_editLabelFunc, jinfo.policy);
							}, this);
							if (!labels.length) {
								labels.push(iwidget.$orgLabel$);
							}
							iwidget._setAllLabels(labels);
						}));
					} else {
						// fallback
						var value = array.map(iinfo, function(item) {
							return item.value;
						});
						iwidget.set('value', value);
					}
				}, this);
			}));
		},

		_openPolicy: function(policyType, policyDN) {
			var props = {
				onObjectSaved: lang.hitch(this, function(dn, policyType) {
					// a new policy was created and should be linked to the current object
					// or an existing policy was modified
					if (!(policyType in this._policyWidgets)) {
						return;
					}
					var policyMultiInput = this._policyWidgets[policyType].$policy$;

					var valuesLoaded = [];
					// trigger a reload of the dynamicValues
					array.forEach(policyMultiInput._widgets, function(subtype) {
						var widget = subtype[0];
						widget.reloadDynamicValues();

						var deferred = new Deferred();
						valuesLoaded.push(deferred);
						// set the value after the reload has been done
						on.once(widget, 'valuesLoaded', lang.hitch(this, function() {
							deferred.resolve();
						}));
					}, this);

					var oldValue = policyMultiInput.get('value');
					var value = policyDN ? lang.clone(oldValue) : [dn];
					var updatePolicy = false;
					if (array.indexOf(value, dn) === -1) {
						value.push(dn);
					} else {
						if (policyDN) {
							updatePolicy = true;
						}
					}
					all(valuesLoaded).then(lang.hitch(this, function() {
						policyMultiInput.set('value', value);
						if (updatePolicy) {
							// we need a manual refresh in case the DN did not change since
							// the policy might have been edited and therefore its values
							// need to be reloaded
							this._updatePolicy(policyType, value);
						}
					}));
				}),
				onCloseTab: lang.hitch(this, function() {
					try {
						this.onFocusModule();
					}
					catch (e) { }
					return true;
				})
			};

			if (policyDN) {
				// policyDN is given, open an existing object
				props.openObject = {
					objectType: policyType,
					objectDN: policyDN,
					note: _('You are currently editing a policy. Changing its properties affects all referenced objects and may affect your system globally.')
				};
			} else {
				// if no DN is given, we are creating a new object
				props.newObject = {
					objectType: policyType
				};
			}

			topic.publish('/umc/modules/open', 'udm', 'policies/policy', props);
		},

		onFocusModule: function() {
			// event stub
		},

		onOptionsChanged: function(newValue) {
			var activeOptions = [];

			// retrieve active options
			var optionsWidget = this._form.widgets.$options$;
			tools.forIn(optionsWidget.get('value'), function(item, value) {
				if (value === true) {
					activeOptions.push(item);
				}
			});

			// hide/show widgets
			tools.forIn(this._propertyOptionMap, lang.hitch(this, function(prop, options) {
				var visible = false;
				if (! (options instanceof Array) || ! options.length ) {
					visible = true;
				} else {
					array.forEach(options, function(option) {
						if (array.indexOf(activeOptions, option) != -1) {
							visible = true;
						}
					});
				}
				var iwidget = this._form.getWidget(prop);
				if (iwidget) {
					iwidget.set('visible' , visible);
				}
			}));

			// hide/show title panes
			this._visibilityTitlePanes(this._layoutMap);
		},

		_anyVisibleWidget: function(titlePane) {
			var visible = false;
			array.forEach(titlePane.layout, lang.hitch(this, function(element) {
				if (element instanceof Array) {
					array.forEach(element, lang.hitch(this, function(property) {
						if (property in this._form._widgets) {
							if (this._form._widgets[ property ].get('visible') === true) {
								visible = true;
								return false;
							}
						}
					}));
					// if there is a visible widget there is no need to check the other widgets
					if (visible) {
						return false;
					}
				} else if (typeof element === "object") {
					if (this._anyVisibleWidget(element)) {
						domClass.toggle(element.$refTitlePane$.domNode, 'dijitDisplayNone', false);
						visible = true;
						return false;
					} else {
						domClass.toggle(element.$refTitlePane$.domNode, 'dijitDisplayNone', true);
					}
				} else if (typeof element === "string" ) {
					var property = element;
					if (property in this._form._widgets) {
						if (this._form._widgets[ property ].get('visible') === true) {
							visible = true;
							return false;
						}
					}
				}
			}));

			return visible;
		},

		_visibilityTitlePanes: function(layout) {
			array.forEach(layout, lang.hitch(this, function(tab) {
				if (typeof tab ===  "object") {
					var visible = false;
					array.forEach(tab.layout, lang.hitch(this, function(element) {
						if (element instanceof Array) {
							if (this._anyVisibleWidget({ layout: element })) {
								visible = true;
							}
							return;
						}
						if (this._anyVisibleWidget(element)) {
							domClass.toggle(element.$refTitlePane$.domNode, 'dijitDisplayNone', false);
							visible = true;
						} else {
							domClass.toggle(element.$refTitlePane$.domNode, 'dijitDisplayNone', true);
						}
					}));
					this._setTabVisibility(tab.$refSubTab$, visible);
				}
			}));
		},

		haveValuesChanged: function() {
			return this._changedValues().length > 0;
		},

		_changedValues: function() {
			var changed = [];
			var regKey = /\$.*\$/;
			tools.forIn(this.getAlteredValues(), function(ikey) {
				if (!regKey.test(ikey) || ikey == '$options$') {
					// key does not start and end with '$' and is thus a regular key
					changed.push(ikey);
				}
			});
			return changed;
		},

		havePolicyReferencesChanged: function() {
			return this._changedPolicyReferenceValues().length > 0;
		},

		_changedPolicyReferenceValues: function() {
			var changed = [];
			tools.forIn(this._policyWidgets, function(ipolicyType, iwidgets) {
				var ival = iwidgets.$policy$.get('value');
				var iresetValue = iwidgets.$policy$._resetValue;
				if (!tools.isEqual(iresetValue, ival)) {
					changed.push(iwidgets);
				}
			}, this);
			return changed;
		},

		haveVisibleValuesChanged: function() {
			if (!this._form) {
				return false;  // not yet loaded
			}
			var valuesChanged = array.some(this._changedValues(), lang.hitch(this, function(key) {
				var widget = this._form.getWidget(key);
				if (!widget) {
					return false;
				}
				return widget.get('visible');
			}));
			return valuesChanged || this.havePolicyReferencesChanged();
		},

		save: function(e) {
			// summary:
			//		Validate the user input through the server and save changes upon success.

			// prevent standard form submission
			if (e) {
				e.preventDefault();
			}

			// get all values that have been altered
			var vals = lang.mixin(this.getEmptyPropsWithDefaultValues(), this.getAlteredValues()); // order is important. overwrite default values from getEmptyPropsWithDefaultValues with altered values

			// reset changed headings
			array.forEach(this._detailPages, function(ipage) {
				// reset the original title (in case we altered it)
				if (ipage.$titleOrig$) {
					ipage.set('title', ipage.$titleOrig$);
					delete ipage.$titleOrig$;
				}
			});

			// reset settings from last validation
			tools.forIn(this._form._widgets, function(iname, iwidget) {
				if (iwidget.setValid) {
					iwidget.setValid(null);
				}
			}, this);

			// validate all widgets to mark invalid/required fields
			this._form.validate();

			// check whether all required properties are set
			var errMessage = '' + _('The following properties need to be specified or are invalid:') + '<ul>';
			var allValuesGiven = true;
			tools.forIn(this._form._widgets, function(iname, iwidget) {
				// ignore widgets that are not visible
				if (!iwidget.get('visible')) {
					return true;
				}

				// in multi-edit mode, ignore widgets that are not marked to be overwritten
				if (this._multiEdit && (!iwidget.$refOverwrite$ || !iwidget.$refOverwrite$.get('value'))) {
					return true;
				}

				// check whether a required property is set or a property is invalid
				var tmpVal = json.stringify(iwidget.get('value'));
				var isEmpty = tmpVal == '""' || tmpVal == '[]' || tmpVal == '{}';
				if ((isEmpty && iwidget.required) || (!isEmpty && iwidget.isValid && false === iwidget.isValid())) {
					// value is empty
					allValuesGiven = false;
					errMessage += '<li>' + iwidget.label + '</li>';
					this._setWidgetInvalid(iname);
				}
			}, this);
			errMessage += '</ul>';

			if (!this.hasEmptyPropsWithDefaultValues() && !this.haveValuesChanged() && !this.havePolicyReferencesChanged()) {
				this.onCloseTab();
				return;  // no changes are made, no need to save an empty dict
			}

			// print out an error message if not all required properties are given
			if (!allValuesGiven) {
				dialog.alert(errMessage);
				return;
			}

			// before storing the values, make a syntax check of the user input on the server side
			var valsNonEmpty = {};
			tools.forIn(vals, function(ikey, ival) {
				if (ikey == this.moduleStore.idProperty) {
					// ignore the ID
					return;
				}
				var tmpVal = json.stringify(ival);
				var isEmpty = tmpVal == '""' || tmpVal == '[]' || tmpVal == '{}';
				if (!isEmpty) {
					valsNonEmpty[ikey] = ival;
				}
			}, this);
			var params = {
				objectType: this._editedObjType,
				properties: valsNonEmpty
			};
			var validationDeferred = this.umcpCommand('udm/validate', params);
			var saveDeferred = new Deferred();
			validationDeferred.then(lang.hitch(this, function(data) {
				// if all elements are valid, save element
				if (this._parseValidation(data.result)) {
					var deferred = null;
					topic.publish('/umc/actions', 'udm', this._parentModule.moduleFlavor, 'edit', 'save');
					// check whether the internal cache needs to be reset
					// as layout, property and default container information may have changed
					var isExtendedAttribute = this.objectType == 'settings/extended_attribute';
					var isUserTemplate = this.objectType == 'settings/usertemplate';
					var isDefaultContainerSetting = this.objectType == 'settings/directory';
					var isContainer = this.objectType == "container/cn" || this.objectType == "container/ou";

					if (isExtendedAttribute || isUserTemplate || isDefaultContainerSetting || isContainer) {
						cache.reset();
					}
					if (this._multiEdit) {
						// save the changes for each object once
						var transaction = this.moduleStore.transaction();
						array.forEach(this.ldapName, function(idn) {
							// shallow copy with corrected DN
							var ivals = lang.mixin({}, vals);
							ivals[this.moduleStore.idProperty] = idn;
							this.moduleStore.put(ivals);
						}, this);
						deferred = transaction.commit();
					} else if (this.operation === 'add' || this.operation === 'copy') {
						deferred = this.moduleStore.add(vals, this.newObjectOptions);
					} else {
						deferred = this.moduleStore.put(vals);
					}
					deferred.then(lang.hitch(this, function(result) {
						// see whether saving was successful
						var success = true;
						var msg = '';
						if (result instanceof Array) {
							msg = '<p>' + _('The following LDAP objects could not be saved:') + '</p><ul>';
							array.forEach(result, function(iresult) {
								success = success && iresult.success;
								if (!iresult.success) {
									msg += lang.replace('<li>{' + this.moduleStore.idProperty + '}: {details}</li>', iresult);
								}
							}, this);
							msg += '</ul>';
						} else {
							success = result.success;
							if (!result.success) {
								msg = _('The LDAP object could not be saved: %(details)s', result);
							}
						}

						if (success && this.moduleFlavor == 'users/self') {
							this.standbyDuring(
								this._loadObject(this._formBuiltDeferred, this._policyDeferred)
							);
							dialog.alert(_('The changes have been successfully applied.'));
							saveDeferred.resolve();
						} else if (success) {
							// everything ok, close page
							this._showUsernameTooLongWarning(data.result);
							this.onCloseTab();
							this.onSave(result.$dn$, this.objectType);
							saveDeferred.resolve();
						} else {
							// print error message to user
							saveDeferred.reject();
							dialog.alert(msg);
						}
					}), lang.hitch(this, function() {
						saveDeferred.reject();
					}));
				} else {
					saveDeferred.reject();
				}
			}));
			var validatedAndSaved = all([validationDeferred, saveDeferred]);
			this.standbyDuring(validatedAndSaved);
			return validatedAndSaved;
		},

		_showUsernameTooLongWarning: function(changedValues) {
			if (this.moduleFlavor !== 'users/user') {
				return;
			}

			var usernameChanged = array.some(changedValues, function(iChangedValue) {
				return iChangedValue.property === 'username';
			});

			var showWarning = usernameChanged && this.usernameMaxLengthChecker.usernameTooLong();
			if (showWarning) {
				var messageData = {
					'length': this.usernameMaxLengthChecker.maxLength
				};
				dialog.warn(lang.replace(this.usernameMaxLengthChecker.warningMessageTemplate, messageData));
			}
		},

		_parseValidation: function(validationList) {
			// summary:
			//		Parse the returned data structure from validation/put/add and check
			//		whether all entries could be validated successfully.

			var allValid = true;
			var errMessage = _('The following properties could not be validated:') + '<ul>';
			array.forEach(validationList, function(iprop) {
				// make sure the form element exists
				var iwidget = this._form._widgets[iprop.property];
				if (!iwidget) {
					return true;
				}

				// iprop.valid and iprop.details may be arrays for properties with
				// multiple values... set all 'true' values to 'null' in order to reset
				// the original items validation mechanism
				var iallValid = iprop.valid;
				var ivalid = iprop.valid === true ? null : iprop.valid;
				if (ivalid instanceof Array) {
					for (var i = 0; i < ivalid.length; ++i) {
						iallValid = iallValid && ivalid[i];
						ivalid[i] = ivalid[i] === true ? null : ivalid[i];
					}
				}
				allValid = allValid && iallValid;

				// check whether form element is valid
				iwidget.setValid(ivalid, iprop.details);
				if (!iallValid) {
					this._setWidgetInvalid(iprop.property);
					var _msg = iprop.details || _('Error');
					if (_msg instanceof Array) {
						_msg = '<ul><li>' + array.filter(iprop.details, function(value) { return value; }).join('</li><li>') + '</li></ul>';
					}

					// update the global error message
					errMessage += '<li>' + _("%(attribute)s: %(message)s\n", {
						attribute: iwidget.label,
						message: _msg
					}) + '</li>';
				}
			}, this);
			errMessage += '</ul>';

			if (!allValid) {
				// upon error, show error message
				dialog.alert(errMessage);
			}

			return allValid;
		},

		_setWidgetInvalid: function(name) {
			// get the widget
			var widget = this._form.getWidget(name);
			if (!widget) {
				return;
			}

			// mark the title of the subtab (in case we have not done it already)
			var page = this._propertySubTabMap[name];
			if (page && !page.$titleOrig$) {
				// store the original title
				page.$titleOrig$ = page.title;
				page.set('title', '<span style="color:red">' + page.title + ' (!)</span>');
			}
		},

		getAlteredValues: function() {
			var _consoleErrorText = lang.hitch(this, function() {
				var text = {
					'users/user'          : _('Failed to retrieve the user from the server.'),
					'groups/group'        : _('Failed to retrieve the group from the server.'),
					'computers/computer'  : _('Failed to retrieve the computer from the server.'),
					'networks/network'    : _('Failed to retrieve the network object from the server.'),
					'dns/dns'             : _('Failed to retrieve the DNS object from the server.'),
					'dhcp/dhcp'           : _('Failed to retrieve the DHCP object from the server.'),
					'shares/share'        : _('Failed to retrieve the share from the server.'),
					'shares/print'        : _('Failed to retrieve the printer from the server.'),
					'mail/mail'           : _('Failed to retrieve the mail object from the server.'),
					'nagios/nagios'       : _('Failed to retrieve the Nagios object from the server.'),
					'policies/policy'     : _('Failed to retrieve the policy from the server.'),
					'settings/portal_all' : _('Failed to retrieve the portal object from the server.')
				}[this.moduleFlavor];
				if (!text) {
					text = _('Failed to retrieve the LDAP object from the server.');
				}return text;
			});

			// summary:
			//		Return a list of object properties that have been altered.

			// get all form values and see which values are new
			var vals = this.getValues();
			var newVals = {};
			if (this._multiEdit) {
				// in multi-edit mode, get all marked entries
				tools.forIn(this._form._widgets, lang.hitch(this, function(iname, iwidget) {
					if (iname === '$options$') {
						var optionVals = {};
						tools.forIn(iwidget._widgets, function(iiname, iiwidget) {
							if (iiwidget.$refOverwrite$ && iiwidget.$refOverwrite$.get('value')) {
								optionVals[iiname] = iiwidget.get('value');
							} else {
								optionVals[iiname] = null;
							}
						});
						var optionsChanged = tools.values(optionVals).some(function(val) {
							return val !== null;
						});
						if (optionsChanged) {
							newVals[iname] = optionVals;
						}
					} else {
						if (iwidget.$refOverwrite$ && iwidget.$refOverwrite$.get('value')) {
							newVals[iname] = iwidget.get('value');
						}
					}
				}));
			} else if (this.operation === 'add' || this.operation === 'copy') {
				// get only non-empty values or values of type 'boolean'
				tools.forIn(vals, lang.hitch(this, function(iname, ival) {
					if (typeof(ival) == 'boolean' || (!(ival instanceof Array && !ival.length) && ival)) {
						newVals[iname] = ival;
					}
				}));
			} else {
				// existing object .. get only the values that changed
				if (this._receivedObjFormData === null) {
					// error happened while loading the object
					setTimeout(lang.hitch(this, 'onCloseTab'), 50); // prevent dom-removal exception with setTimeout
					console.error(_consoleErrorText());
					return {};
				}
				tools.forIn(vals, function(iname, ival) {
					var oldVal = this._receivedObjFormData[iname];

					// check whether old and new values differ...
					if (!tools.isEqual(ival,oldVal)) {
						newVals[iname] = ival;
					}
				}, this);

				// set the LDAP DN
				newVals[this.moduleStore.idProperty] = vals[this.moduleStore.idProperty];
			}

			return newVals;
		},

		getEmptyPropsWithDefaultValues: function() {
			var emptyPropsWithDefaultValues = {};
			tools.forIn(lang.getObject('_receivedObjOrigData.$empty_props_with_default_set$', false, this) || {}, lang.hitch(this, function(key, value) {
				// Ignore empty props with default values if they are not in the form.
				// This can e.g. happen for the users/self module since all properties are gathered from
				// users/user but only a few are in the form. (Bug #48047)
				if (this._receivedObjFormData.hasOwnProperty(key)) {
					emptyPropsWithDefaultValues[key] = value.default_value;
				}
			}));
			return emptyPropsWithDefaultValues;
		},

		hasEmptyPropsWithDefaultValues: function() {
			var hasEmptyPropsWithDefaultValues = false;
			tools.forIn(lang.getObject('_receivedObjOrigData.$empty_props_with_default_set$', false, this) || {}, function() {
				hasEmptyPropsWithDefaultValues = true;
				return false; // short circuit forIn()
			});
			return hasEmptyPropsWithDefaultValues;
		},

		shouldPreventPopupForEmptyPropWithDefault: function(propName) {
			var emptyProps = lang.getObject('_receivedObjOrigData.$empty_props_with_default_set$', false, this) || {};
			return (emptyProps[propName] && emptyProps[propName].prevent_umc_default_popup) || false;
		},

		confirmClose: function() {
			topic.publish('/umc/actions', 'udm', this._parentModule.moduleFlavor, 'edit', 'cancel');

			if (this.operation === 'edit' && this.haveVisibleValuesChanged()) {
				return dialog.confirm(_('There are unsaved changes. Are you sure to cancel?'), [{
					label: _('Continue editing'),
					name: 'cancel'
				}, {
					label: _('Discard changes'),
					name: 'quit',
					'default': true,
					callback: lang.hitch(this, 'onCloseTab')
				}]);
			}
			this.onCloseTab();
		},

		onCloseTab: function() {
			// summary:
			//		Event is called when the page should be closed.
			return true;
		},

		onSave: function(dn, objectType) {
			// event stub
		}
	});
});
