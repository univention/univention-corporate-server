/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._udm.DetailPage");

dojo.require("dijit.TitlePane");
dojo.require("dijit.layout.BorderContainer");
dojo.require("dijit.layout.ContentPane");
dojo.require("dojo.string");
dojo.require("dojo.DeferredList");
dojo.require("umc.i18n");
dojo.require("umc.modules._udm.Template");
dojo.require("umc.render");
dojo.require("umc.tools");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.WidgetGroup");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TabContainer");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.modules._udm.DetailPage", [ dijit.layout.ContentPane, umc.widgets._WidgetsInWidgetsMixin, umc.i18n.Mixin ], {
	// summary:
	//		This class renderes a detail page containing subtabs and form elements
	//		in order to edit UDM objects.

	// umcpCommand: Function
	//		Reference to the module specific umcpCommand function.
	umcpCommand: null,

	// moduleStore: Object
	//		Reference to the module's module store.
	moduleStore: null,

	// moduleFlavor: String
	//		Flavor of the module
	moduleFlavor: this.moduleFlavor,

	// objectType: String
	//		The object type of the UDM object that is edited.
	objectType: null,

	// ldapName: String?
	//		The LDAP DN of the object that is edited. This property needs not to be set
	//		when a new object is edited.
	ldapName: null,

	// newObjectOptions:
	// 		Dict containing options for creating a new UDM object (chosen by the user
	// 		in the 'add object' dialog). This includes properties such as superordinate,
	//		the container in wich the object is to be created, the object type etc.
	newObjectOptions: null,

	// isCloseable: Boolean?
	//		Specifies whether this 
	isClosable: false,

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.udm',

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	// internal reference to the page containing the subtabs for object properties
	_tabs: null,

	// internal reference to a dict with entries of the form: policy-type -> widgets
	_policyWidgets: null,

	// dojo.Deferred object of the query and render process for the policy widgets
	_policyDeferred: null,

	// object properties as they are received from the server
	_receivedObjOrigData: null,

	// initial object properties as they are represented by the form
	_receivedObjFormData: null,

	// UDM object type of the current edited object
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

	// the widget of the options if available
	_optionsWidget: null,

	// reference to the template object in order to monitor user input changes
	_template: null,

	buildRendering: function() {
		// summary:
		//		Query necessary information from the server for the object detail page
		//		and initiate the rendering process.
		this.inherited(arguments);

		// remember the objectType of the object we are going to edit
		this._editedObjType = this.objectType;

		// for the detail page, we first need to query property data from the server
		// for the layout of the selected object type, then we can render the page
		var params = {
			objectType: this.objectType,
			objectDN: this.ldapName || null
		};

		var commands = [
			this.umcpCommand('udm/properties', params),
			this.umcpCommand('udm/layout', params),
			this.umcpCommand('udm/policies', params)
		];

		// in case an object template has been chosen, add the umcp request for the template
		var objTemplate = dojo.getObject('objectTemplate', false, this.newObjectOptions);
		if (objTemplate && 'None' != objTemplate) {
			commands.push(this.umcpCommand('udm/get', [objTemplate], true, 'settings/usertemplate'));
		}

		// when the commands have been finished, create the detail page
		(new dojo.DeferredList(commands)).then(dojo.hitch(this, function(results) {
			var properties = results[0][1].result;
			var layout = results[1][1].result;
			var policies = results[2][1].result;
			var template = results.length > 3 ? results[3][1].result : null;
			this.renderDetailPage(properties, layout, policies, template);
		}));
	},

	renderDetailPage: function(_properties, _layout, policies, _template) {
		// summary:
		//		Render the form with subtabs containing all object properties that can
		//		be edited by the user.

		// create detail page
		this._tabs = new umc.widgets.TabContainer({
			nested: true,
			region: 'center'
		});

		// parse the widget configurations
		var properties = [];
		var optionMap = {};
		dojo.forEach(_properties, function(iprop) {
			// ignore internal properties
			if ( iprop.id.slice( 0, 1 ) == '$' && iprop.id.slice( -1 ) == '$' ) {
				properties.push(iprop);
				return;
			}
			if ( 'LinkList' == iprop.type ) {
				iprop.multivalue = false;
			} else if ( iprop.type.indexOf('MultiObjectSelect') >= 0 ) {
				iprop.multivalue = false;
			} else if (iprop.multivalue && 'MultiInput' != iprop.type) {
				// handle multivalue inputs
				iprop.subtypes = [{
					type: iprop.type,
					dynamicValues: iprop.dynamicValues,
					dynamicOptions: iprop.dynamicOptions,
					staticValues: iprop.staticValues
				}];
				iprop.type = 'MultiInput';
			}
			iprop.disabled = this.ldapName === undefined ? false :  ! iprop.editable;
			properties.push(iprop);
			optionMap[ iprop.id ] = iprop.options;
		}, this);
		this._propertyOptionMap = optionMap;

		// ### Advanved settings
		// parse the layout configuration... we would like to group all groups of advanced
		// settings on a special sub tab
		var advancedGroup = {
			label: this._('[Advanced settings]'),
			description: this._('Advanced settings'),
			layout: []
		};
		var layout = [];
		dojo.forEach(_layout, function(ilayout) {
			if (ilayout.advanced) {
				// advanced groups of settings should go into one single sub tab
				var jlayout = dojo.mixin({ open: false }, ilayout);
				advancedGroup.layout.push(jlayout);
			}
			else {
				layout.push(ilayout);
			}
		});
		// if there are advanced settings, add them to the layout
		if (advancedGroup.layout.length) {
			layout.push(advancedGroup);
		}

		// ### Options
		var option_values = {};
		var option_prop = null;
		dojo.forEach( properties, function( item ) {
			if ( item.id == '$options$' ) {
				option_prop = item;
				return false;
			}
		} );
		if ( option_prop && option_prop.widgets.length > 0 ) {
			var optiontab = {
				label: this._( '[Options]' ),
				description: this._( 'Options describing the basic features of the UDM object' ),
				layout: [ '$options$' ]
			};
			layout.push( optiontab );

			var option_widgets = [];
			var option_layout = [];
			var create = this.ldapName === undefined;
			dojo.forEach( option_prop.widgets, function ( option ) {
				option_widgets.push( dojo.mixin( {
					disabled: create ? false : ! option.editable
				}, option ) );
				option_values[ option.id ] = option.value;
				option_layout.push( option.id );
			} );
			option_prop.widgets = option_widgets;
			option_prop.layout = option_layout;
		} else {
			properties = dojo.filter( properties, function( item ) {
				return item.id != '$options$';
			} );
		}

		// special case for password, it is only required when a new user is added
		if (!this.newObjectOptions) {
			dojo.forEach(properties, function(iprop) {
				if ('password' == iprop.id) {
					iprop.required = false;
					return false;
				}
			});
		}

		// make sure that the widget use the flavored umcpCommand
		dojo.forEach( properties, function( iprop ) {
			iprop.umcpCommand = this.umcpCommand;
		}, this );


		// render all widgets
		var widgets = umc.render.widgets( properties );

		// connect to onChange for the options property if it exists
		if ( '$options$' in widgets ) {
			this._optionsWidget = widgets.$options$;
			this.connect( this._optionsWidget, 'onChange', 'onOptionsChanged' );
		}

		// find property identifying the object
		umc.tools.forIn( widgets, function( name, widget ) {
							 if ( widget.identifies ) {
								 // connect to onChange and modify title using this.parentWidget.set( 'title', ... )
								 this.connect( widget, 'onChange', dojo.hitch( this, function( value ) {
												   this.moduleWidget.set( 'title', this.moduleWidget.defaultTitle + ': ' + value );
											   } ) );
								 return false; // break out of forIn
							 }
						 }, this );

		// render the layout for each subtab
		this._propertySubTabMap = {}; // map to remember which form element is displayed on which subtab
		this._detailPages = [];
		dojo.forEach(layout, function(ilayout) {
			// create a new page, i.e., subtab
			var subTab = new umc.widgets.Page({
				title: ilayout.label || ilayout.name, //TODO: 'name' should not be necessary
				noFooter: true,
				headerText: ilayout.description || ilayout.label || ilayout.name,
				helpText: ''
			});

			// add rendered layout to subtab and register subtab
			var subTabWidgets = umc.render.layout(ilayout.layout, widgets);
			ilayout.$refSubTab$ = subTab;
			dojo.style(subTabWidgets.domNode, 'overflow', 'auto');
			subTab.addChild(subTabWidgets);
			this._tabs.addChild(subTab);

			// update _propertySubTabMap
			this._detailPages.push(subTab);
			var layoutStack = [ ilayout.layout ];
			while (layoutStack.length) {
				var ielement = layoutStack.pop();
				if (dojo.isArray(ielement)) {
					layoutStack = layoutStack.concat(ielement);
				}
				else if (dojo.isString(ielement)) {
					this._propertySubTabMap[ielement] = subTab;
				}
				else if (ielement.layout) {
					layoutStack.push(ielement.layout);
				}
			}
		}, this);
		this._layoutMap = layout;

		if ( '$options$' in widgets ) {
			// required when creating a new object
			this._optionsWidget.set( 'value', option_values );
		}

		// #### Policies
		// in case we have policies that apply to the current object, we need an extra
		// sub tab that groups all policies together
		this._policyWidgets = {};
		if (policies && policies.length) {
			this._policiesTab = new umc.widgets.Page({
				title: this._('[Policies]'),
				noFooter: true,
				headerText: this._('Properties inherited from policies'),
				helpText: this._('List of all object properties that are inherited by policies. The values cannot be edited directly. In order to edit a policy, click on the "edit" button to open a particular policy in a new tab.')
			});
			this._tabs.addChild(this._policiesTab);
			var policiesContainer = new umc.widgets.ContainerWidget({
				scrollable: true
			});
			this._policiesTab.addChild(policiesContainer);

			// we need to query for each policy object its properties and its layout
			// this can be done asynchronously
			var commands = [];
			dojo.forEach(policies, function(ipolicy) {
				var params = { objectType: ipolicy.objectType };
				commands.push(this.umcpCommand('udm/properties', params));
				commands.push(this.umcpCommand('udm/layout', params));
			}, this);

			// wait until we have results for all queries
			this._policyDeferred = (new dojo.DeferredList(commands)).then(dojo.hitch(this, function(results) {
				// parse the widget configurations
				var layout = [];
				var widgetConfs = [];
				var i;
				for (i = 0; i < results.length; i += 2) {
					var ipolicy = policies[Math.floor(i / 2)];
					var ipolicyType = ipolicy.objectType;
					var iproperties = results[i][1].result;
					var ilayout = results[i + 1][1].result;
					var newLayout = [];

					// we only need to show the general properties of the policy... the "advanced"
					// properties would be rendered on the subtab "advanced settings" which we do
					// not need in this case
					dojo.forEach(ilayout, function(jlayout) {
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
					dojo.forEach(newLayout, function(jlayout, j) {
					   if ( dojo.isArray( jlayout ) || dojo.isObject( jlayout ) ) {
						   var nestedLayout = undefined === jlayout.layout ? jlayout : jlayout.layout;
							dojo.forEach( nestedLayout, function(klayout, k) {
								dojo.forEach(umc.tools.stringOrArray(klayout), function(llayout) {
									if (dojo.isString(llayout)) {
										if ('name' != llayout) {
											usedProperties[llayout] = true;
										}
									}
								});
							});
						} else if (dojo.isString(jlayout)) {
							if ('name' != jlayout) {
								usedProperties[jlayout] = true;
							}
						}
					});

					// get only the properties that need to be rendered
					var newProperties = [];
					dojo.forEach(iproperties, function(jprop) {
						var jname = jprop.id || jprop.name;
						if (jname in usedProperties) {
							if (jprop.multivalue && 'MultiInput' != jprop.type) {
								// handle multivalue inputs
								jprop.subtypes = [{ type: jprop.type }];
								jprop.type = 'MultiInput';
							}
							jprop.disabled = true; // policies cannot be edited
							jprop.$orgLabel$ = jprop.label; // we need the original label
							newProperties.push(jprop);
						}
					}, this);

					// make sure that the widget use the flavored umcpCommand
					dojo.forEach( newProperties, function( iprop ) {
						iprop.umcpCommand = this.umcpCommand;
					}, this );

					// for the policy group, we need a ComboBox that allows to link an object
					// to a particular policy
					newProperties.push({
						type: 'ComboBox',
						name: '$policy$',
						staticValues: [{ id: 'None', label: this._('Inherited') }],
						dynamicValues: dojo.hitch(this, '_queryPolicies', ipolicyType),
						label: this._('Select policy configuration'),
						description: this._('Select a policy that should be directly linked to the current UDM object'),
						onChange: dojo.hitch(this, '_updatePolicy', ipolicyType)
					});
					var buttonsConf = [{
						type: 'Button',
						name: '$addPolicy$',
						label: this._('Create new policy'),
						callback: dojo.hitch(this, '_openPolicy', ipolicyType, undefined)
					}];
					newLayout.unshift(['$policy$', '$addPolicy$']);

					// render the group of properties
					var widgets = umc.render.widgets(newProperties);
					this._policyWidgets[ipolicyType] = widgets;
					var buttons = umc.render.buttons(buttonsConf);
					policiesContainer.addChild(new dijit.TitlePane({
						title: ipolicy.label,
						description: ipolicy.description,
						open: false,
						content: umc.render.layout(newLayout, widgets, buttons)
					}));
				}
			}));
		}
		else {
			// in case there are no policies, we use a dummy Deferred object
			this._policyDeferred = new dojo.Deferred();
			this._policyDeferred.resolve();
		}

		// finished adding sub tabs for now
		this._tabs.startup();

		// setup detail page, needs to be wrapped by a form (for managing the
		// form entries) and a BorderContainer (for the footer with buttons)
		var borderLayout = this.adopt(dijit.layout.BorderContainer, {
			gutters: false
		});
		borderLayout.addChild(this._tabs);

		var closeLabel = this._('Back to search');
		if ('navigation' == this.moduleFlavor) {
			closeLabel = this._('Back to navigation');
		}
		if (this.isClosable) {
			closeLabel = this._('Cancel');
		}

		// buttons
		var buttons = umc.render.buttons([{
			name: 'submit',
			label: this._('Save changes'),
			style: 'float: right'
		}, {
			name: 'close',
			label: closeLabel,
			callback: dojo.hitch(this, 'onClose'),
			style: 'float: left'
		}]);
		var footer = new umc.widgets.ContainerWidget({
			'class': 'umcPageFooter',
			region: 'bottom'
		});
		dojo.forEach(buttons.$order$, function(i) {
			footer.addChild(i);
		});
		borderLayout.addChild(footer);
		borderLayout.startup();

		// create the form containing the whole BorderContainer as content and add
		// the form as content of this class
		this._form = this.adopt(umc.widgets.Form, {
			widgets: widgets,
			content: borderLayout,
			moduleStore: this.moduleStore,
			onSubmit: dojo.hitch(this, 'validateChanges')
		});
		this.set('content', this._form);

		// search for given default values in the properties... these will be replaced
		// by the template mechanism
		var template = {};
		dojo.forEach(_properties, function(iprop) {
			if (iprop['default']) {
				var defVal = iprop['default'];
				if (dojo.isString(defVal) && iprop.multivalue) {
					defVal = [ defVal ];
				}
				template[iprop.id] = defVal;
			}
		});

		// mixin the values set in the template object (if given)
		if (_template && _template.length > 0) {
			// remove first the template's LDAP-DN
			_template = _template[0];
			delete _template.$dn$;
			template = dojo.mixin(template, _template);
		}

		// create a new template object that takes care of updating the elements in the form
		this._template = this.adopt(umc.modules._udm.Template, {
			widgets: widgets,
			template: template
		});

		// load form data
		if (this.ldapName) {
			this._form.load(this.ldapName).then(dojo.hitch(this, function(vals) {
				// save the original data we received from the server
				this._receivedObjOrigData = vals;

				// as soon as the policy widgets are rendered, update the policy values
				this._policyDeferred.then(dojo.hitch(this, function() {
					var policies = dojo.getObject('_receivedObjOrigData.$policies$', false, this) || {};
					umc.tools.forIn(policies, function(ipolicyType, ipolicyDN) {
						// get the ComboBox to update its value with the new DN
						if (ipolicyType in this._policyWidgets) {
							var iwidget = this._policyWidgets[ipolicyType].$policy$;
							iwidget.setInitialValue(ipolicyDN, true);
						}
					}, this);
				}));

				// save the original form data
				this._receivedObjFormData = this.getValues();
			}));
		}
	},

	getValues: function() {
		// get all form values
		var vals = this._form.gatherFormValues();
		
		// get also policy values... can not be handled as standard form entry
		vals.$policies$ = {};
		umc.tools.forIn(this._policyWidgets, function(ipolicyType, iwidgets) {
			var ival = iwidgets.$policy$.get('value');
			if ('None' != ival) {
				vals.$policies$[ipolicyType] = ival;
			}
		}, this);

		return vals;
	},

	_queryPolicies: function(objectType) {
		return this.umcpCommand('udm/query', { 
			objectType: objectType,
			container: 'all', 
			objectProperty: 'None',
			objectPropertyValue: ''
		}).then(function(data) {
			return dojo.map(data.result, function(ientry) {
				return ientry.$dn$;
			});
		});
	},

	_updatePolicy: function(policyType, policyDN) {
		// make sure the given policyType exists
		if (!(policyType in this._policyWidgets)) {
			return;
		}

		// evaluate the policy with the given policyType and policyDN
		this.umcpCommand('udm/object/policies', {
			objectType: this.objectType,
			policyDN: 'None' == policyDN || !policyDN ? null : policyDN,
			policyType: policyType,
			objectDN: this.ldapName || null,
			container: this.newObjectOptions ? this.newObjectOptions.container : null
		}).then(dojo.hitch(this, function(data) {
			umc.tools.forIn(data.result, function(iname, iinfo) {
				// ensure that the given property name exists for the policy
				var iwidget = this._policyWidgets[policyType][iname];
				if (!iwidget) {
					return true;
				}

				// set the value and label
				if (!dojo.isArray(iinfo)) {
					// standard policy
					iwidget.set('value', iinfo.value);
					var label = dojo.replace('{label} (<a href="javascript:void(0)" ' +
							'onclick=\'dijit.byId("{id}")._openPolicy("{type}", "{dn}")\' ' +
							'title="{title}: {dn}">{edit}</a>)', {
						label: iwidget.$orgLabel$,
						id: this.id,
						type: policyType,
						dn: iinfo.policy,
						title: this._('Click to edit the inherited properties of the policy'),
						edit: this._('edit')
					});
					iwidget.set('label', label);
				}
				else if (dojo.isArray(iinfo) && umc.tools.inheritsFrom(iwidget, 'umc.widgets.MultiInput')) {
					// we got probably a UCR-Policy, this is a special case:
					// -> a list of values where each value might have been inherited 
					//    by different policies
					iwidget.set('value', dojo.map(iinfo, function(ival) {
						return ival.value;
					}));

					dojo.forEach(iinfo, function(jinfo, j) {
						if (iwidget._rowContainers.length < j) {
							// something is wrong... there are not enough entries it seems
							return false;
						}

						// prepare the HTML code to link to the policy
						var label = dojo.replace('(<a href="javascript:void(0)" ' +
								'onclick=\'dijit.byId("{id}")._openPolicy("{type}", "{dn}")\' ' +
								'title="{title}: {dn}">{edit}</a>)', {
							id: this.id,
							type: policyType,
							dn: jinfo.policy,
							title: this._('Click to edit the inherited properties of the policy'),
							edit: this._('edit')
						});

						var container = iwidget._rowContainers[j];
						if (!container.$linkWidget$) {
							// add an additional widget with the link the the UCR policy to the row
							container.$linkWidget$ = new umc.widgets.LabelPane({ 
								label: j == 0 ? '&nbsp;' : '',
								content: new umc.widgets.Text({ 
									content: label 
								}) 
							});

							// get the correct row container
							container.addChild(container.$linkWidget$);
						}
						else {
							// link widget already exists, update its content
							container.$linkWidget$.set('content', label);
						}
					}, this);

					// make sure that the last row does not contain a link widget
					var lastContainer = iwidget._rowContainers[iwidget._rowContainers.length - 1];
					if (lastContainer.$linkWidget$) {
						lastContainer.removeChild(lastContainer.$linkWidget$);
						lastContainer.$linkWidget$.destroyRecursive();
						lastContainer.$linkWidget$ = null;
					}
				} 
				else {
					// fallback
					var value = dojo.map( iinfo, function( item ) {
						return item.value;
					} );
					iwidget.set('value', value);
				}
			}, this);
		}));
	},

	_openPolicy: function(policyType, policyDN) {
		var props = {
			onObjectSaved: dojo.hitch(this, function(dn, policyType) {
				// a new policy was created and should be linked to the current object
				// or an existing policy was modified
				if ((policyType in this._policyWidgets)) {
					// trigger a reload of the dynamicValues
					var widget = this._policyWidgets[policyType].$policy$;
					widget.reloadDynamicValues();

					// set the value after the reload has been done
					var handle = this.connect(widget, 'onValuesLoaded', dojo.hitch(this, function() {
						this.disconnect(handle);
						var oldDN = widget.get('value');
						widget.set('value', dn);
						if (oldDN == dn) {
							// we need a manual refresh in case the DN did not change since
							// the policy might have been edited and therefore its values
							// need to be reloaded
							this._updatePolicy(policyType, dn);
						}
					}));
				}
			}),
			onClose: dojo.hitch(this, function() {
				this.onFocusModule();
				return true;
			})
		};

		if (policyDN) {
			// policyDN is given, open an existing object
			props.openObject = {
				objectType: policyType,
				objectDN: policyDN
			};
		}
		else {
			// if no DN is given, we are creating a new oject
			props.newObject = {
				objectType: policyType
			};
		}

		dojo.publish("/umc/modules/open", ["udm", "policies/policy", props]);
	},

	onFocusModule: function() {
		// event stub
	},

	onOptionsChanged: function( newValue, widgetName ) {
		var activeOptions = [];

		// retrieve active options
		umc.tools.forIn( this._optionsWidget.get( 'value' ), function( item, value ) {
			if ( value === true ) {
				activeOptions.push( item );
			}
		} );

		// hide/show widgets
		umc.tools.forIn( this._propertyOptionMap, dojo.hitch( this, function( prop, options ) {
			var visible = false;
			if ( ! dojo.isArray( options ) || ! options.length  ) {
				visible = true;
			} else {
				dojo.forEach( options, function( option ) {
					if ( activeOptions.indexOf( option ) != -1 ) {
						visible = true;
					}
				} );
			}
			var iwidget = this._form.getWidget( prop );
			if (iwidget) {
				iwidget.set( 'visible' , visible );
			}
		} ) );

		// hide/show title panes
		this._visibilityTitlePanes( this._layoutMap );
	},

	_anyVisibleWidget: function( titlePane ) {
		var visible = false;
		dojo.forEach( titlePane.layout, dojo.hitch( this, function( element ) {
			if ( dojo.isArray( element ) ) {
				dojo.forEach( element, dojo.hitch( this, function( property ) {
					if ( property in this._form._widgets ) {
						if ( this._form._widgets[ property ].get( 'visible' ) === true ) {
							visible = true;
							return false;
						}
					}
				} ) );
				// if there is a visible widget there is no need to check the other widgets
				if ( visible ) {
					return false;
				}
			} else if ( dojo.isObject( element ) ) {
				if ( this._anyVisibleWidget( element ) ) {
					dojo.toggleClass( element.$refTitlePane$.domNode, 'dijitHidden', false );
					visible = true;
					return false;
				} else {
					dojo.toggleClass( element.$refTitlePane$.domNode, 'dijitHidden', true );
				}
			}
		} ) );

		return visible;
	},

	_visibilityTitlePanes: function( layout ) {
		dojo.forEach( layout, dojo.hitch( this, function( tab ) {
			if ( dojo.isObject( tab ) ) {
				var visible = false;
				dojo.forEach( tab.layout, dojo.hitch( this, function( element ) {
					if ( dojo.isArray( element ) ) {
						// ignore for now
						visible = true;
						return;
					}
					if ( this._anyVisibleWidget( element ) ) {
						dojo.toggleClass( element.$refTitlePane$.domNode, 'dijitHidden', false );
						visible = true;
					} else {
						dojo.toggleClass( element.$refTitlePane$.domNode, 'dijitHidden', true );
					}
				} ) );
				if ( ! visible ) {
					this._tabs.hideChild( tab.$refSubTab$ );
				} else {
					this._tabs.showChild( tab.$refSubTab$ );
				}
			}
		} ) );
	},

	validateChanges: function(e) {
		// summary:
		//		Validate the user input through the server and save changes upon success.

		// prevent standard form submission
		e.preventDefault();

		// get all values that have been altered
		var vals = this.getAlteredValues();

		// copy dict and remove the ID
		var valsNoID = dojo.mixin({}, vals);
		delete valsNoID[this.moduleStore.idProperty];

		// reset changed headings
		dojo.forEach(this._detailPages, function(ipage) {
			// reset the original title (in case we altered it)
			if (ipage.$titleOrig$) {
				ipage.set('title', ipage.$titleOrig$);
				delete ipage.$titleOrig$;
			}
		});

		// reset settings from last validation
		umc.tools.forIn(this._form._widgets, function(iname, iwidget) {
			if (iwidget.setValid) {
				iwidget.setValid(null);
			}
		}, this);

		// check whether all required properties are set
		var errMessage = '' + this._('The following properties need to be specified or are invalid:') + '<ul>';
		var allValuesGiven = true;
		umc.tools.forIn(this._form._widgets, function(iname, iwidget) {
			// ignore widgets that are not visible
			if (!iwidget.get('visible')) {
				return true;
			}

			// check whether a required property is set or a property is invalid
			var tmpVal = dojo.toJson(iwidget.get('value'));
			var isEmpty = tmpVal == '""' || tmpVal == '[]' || tmpVal == '{}';
			if ((isEmpty && iwidget.required) || (!isEmpty && iwidget.isValid && false === iwidget.isValid())) {
				// value is empty
				allValuesGiven = false;
				errMessage += '<li>' + iwidget.label + '</li>';
				this._setWidgetInvalid(iname);
			}
		}, this);
		errMessage += '</ul>';

		// print out an error message if not all required properties are given
		if (!allValuesGiven) {
			umc.dialog.alert(errMessage);
			return;
		}

		// before storing the values, make a syntax check of the user input on the server side
		var params = {
			objectType: this._editedObjType,
			properties: valsNoID
		};
		this.umcpCommand('udm/validate', params).then(dojo.hitch(this, function(data) {
			// if all elements are valid, save element
			if (this._parseValidation(data.result)) {
				this.saveChanges(vals);
			}
		}));
	},

	_parseValidation: function(validationList) {
		// summary:
		//		Parse the returned data structure from validation/put/add and check
		//		whether all entries could be validated successfully.

		var allValid = true;
		var errMessage = this._('The following properties could not be validated:') + '<ul>';
		dojo.forEach(validationList, function(iprop) {
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
			if (dojo.isArray(ivalid)) {
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

				// update the global error message
				errMessage += '<li>' + this._("%(attribute)s: %(message)s\n", {
					attribute: iwidget.label,
					message: iprop.details || this._('Error')
				}) + '</li>';
			}
		}, this);
		errMessage += '</ul>';

		if (!allValid) {
			// upon error, show error message
			umc.dialog.alert(errMessage);
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

	saveChanges: function(vals) {
		// summary:
		//		Save the user changes for the edited object.

		var deffered = null;
		if (this.newObjectOptions) {
			deffered = this.moduleStore.add(vals, this.newObjectOptions);
		}
		else {
			deffered = this.moduleStore.put(vals);
		}
		deffered.then(dojo.hitch(this, function(result) {
			if (result.success) {
				this.onClose();
				this.onSave(result.$dn$, this.objectType);
			}
			else {
				umc.dialog.alert(this._('The UDM object could not be saved: %(details)s', result));
			}
		}));
	},

	getAlteredValues: function() {
		// summary:
		//		Return a list of object properties that have been altered.

		// get all form values and see which values are new
		var vals = this.getValues();
		var newVals = {};
		if (this.newObjectOptions) {
			// get only non-empty values
			umc.tools.forIn(vals, dojo.hitch(this, function(iname, ival) {
				if (!(dojo.isArray(ival) && !ival.length) && ival) {
					newVals[iname] = ival;
				}
			}));
		}
		else {
			// existing object .. get only the values that changed
			umc.tools.forIn(vals, function(iname, ival) {
				var oldVal = this._receivedObjFormData[iname];

				// check whether old values and new values differ...
				// convert to JSON since we may have dicts/arrays as value
				if (dojo.toJson(ival) != dojo.toJson(oldVal)) {
					newVals[iname] = ival;
				}
			}, this);

			// set the LDAP DN
			newVals[this.moduleStore.idProperty] = vals[this.moduleStore.idProperty];
		}
		return newVals;
	},

	onClose: function() {
		// summary:
		//		Event is called when the page should be closed.
		return true;
	},

	onSave: function(dn, objectType) {
		// event stub
	}
});



