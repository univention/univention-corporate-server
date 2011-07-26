/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._udm.DetailPage");

dojo.require("umc.widgets._WidgetsInWidgetsMixin");
dojo.require("dijit.layout.ContentPane");

dojo.declare("umc.modules._udm.DetailPage", [ dijit.layout.ContentPane, umc.widgets._WidgetsInWidgetsMixin, umc.i18n.Mixin ], {
	// summary:
	//		
	// description:

	// umcpCommand: Function
	//		Reference to the module specific umcpCommand function.
	umcpCommand: null,

	moduleStore: null,

	objectType: null,

	ldapName: null,

	// newObjectOptions:
	// 		Dict containing options for creating a new UDM object (chosen by the user
	// 		in the 'add object' dialog). This includes properties such as superordinate,
	//		the container in wich the object is to be created, the object type etc.
	newObjectOptions: null,
	
	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.udm',

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	// internal reference to the page containing the subtabs for object properties
	_tabs: null,

	// object properties as they are received from the server
	_receivedObjOrigData: null,

	// initial object properties as they are represented by the form
	_receivedObjFormData: null,

	// UDM object type of the current edited object
	_editedObjType: null,

	// dict that saves which form element is displayed on which subtab
	// (used to display user input errors)
	_propertySubTabMap: null,

	// array that stores extra references to all sub tabs
	// (necessary to reset change sub tab titles [when displaying input errors])
	_detailPages: null,

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
		var params = { objectType: this.objectType };
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

	renderDetailPage: function(_properties, _layout, policies, template) {
		// summary:
		//		Render the form with subtabs containing all object properties that can
		//		be edited by the user.

		// create detail page
		this._tabs = new dijit.layout.TabContainer({
			nested: true,
			region: 'center'
		});

		// parse the widget configurations
		var properties = [];
		dojo.forEach(_properties, function(iprop) {
			if ('ComplexInput' == iprop.type) {
				// handle complex widgets
				iprop.type = 'MultiInput';
			}
			if (iprop.multivalue && 'MultiInput' != iprop.type) {
				// handle multivalue inputs
				iprop.subtypes = [{ type: iprop.type }];
				iprop.type = 'MultiInput';
			}
			properties.push(iprop);
		});

		// parse the layout configuration... we would like to group all groups of advanced 
		// settings on a special sub tab
		var advancedGroup = {
			label: this._('Advanced settings'),
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

		// render all widgets
		var widgets = umc.tools.renderWidgets(properties);

		// render the layout for each subtab
		this._propertySubTabMap = {}; // map to remember which form element is displayed on which subtab
		this._detailPages = [];
		dojo.forEach(layout, function(ilayout) {
			// create a new page, i.e., subtab
			var subTab = new umc.widgets.Page({
				title: ilayout.label || ilayout.name //TODO: 'name' should not be necessary
			});

			// add rendered layout to subtab and register subtab
			subTab.addChild(umc.tools.renderLayout(ilayout.layout, widgets));
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

		// finished adding sub tabs for now
		this._tabs.startup();

		// in case we have policies that apply to the current object, we need an extra
		// sub tab that groups all policies together:e 
		var policyGroups;

		// setup detail page, needs to be wrapped by a form (for managing the
		// form entries) and a BorderContainer (for the footer with buttons)
		var borderLayout = this.adopt(dijit.layout.BorderContainer, {});
		borderLayout.addChild(this._tabs);

		// buttons
		var buttons = umc.tools.renderButtons([{
			name: 'submit',
			label: this._('Save changes')
		}, {
			name: 'close',
			label: 'navigation' == this.moduleFlavor ? this._('Back to navigation') : this._('Back to search'),
			callback: dojo.hitch(this, 'onClose')
		}]);
		var footer = new umc.widgets.ContainerWidget({
			region: 'bottom',
			'class': 'umcNoBorder'
		});
		dojo.forEach(buttons._order, function(i) { 
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

		// in case we have a template, create a new template object that takes care
		// of updating the elements in the form
		if (template && template.length > 0) {
			this._template = this.adopt(umc.modules._udm.Template, {
				widgets: widgets,
				template: template[0]
			});
		}

		// load form data
		if (this.ldapName) {
			this._form.load(this.ldapName).then(dojo.hitch(this, function(vals) {
				this._receivedObjOrigData = vals;
				this._receivedObjFormData = this._form.gatherFormValues();
			}));
		}
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

		// before storing the values, make a syntax check of the user input on the server side
		var params = {
			objectType: this._editedObjType,
			properties: valsNoID
		};
		this.umcpCommand('udm/validate', params).then(dojo.hitch(this, function(data) {
			var validation = data.result;
			var allValid = true;
			dojo.forEach(data.result, function(iprop) {
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
					// mark the title of the subtab (in case we have not done it already)
					var ipage = this._propertySubTabMap[iprop.property];
					if (ipage && !ipage.$titleOrig$) {
						// store the original title
						ipage.$titleOrig$ = ipage.title;
						ipage.set('title', '<span style="color:red">' + ipage.title + ' (!)</span>');
					}
				}
			}, this);

			// if all elements are valid, save element
			if (allValid) {
				this.saveChanges(vals);
			}
		}));
	},

	saveChanges: function(vals) {
		// summary:
		//		Save the user changes for the edited object.

		console.log(vals);

		var deffered = null;
		if (this.newObjectOptions) {
			deffered = this.moduleStore.add(vals, this.newObjectOptions);
		}
		else {
			deffered = this.moduleStore.put(vals);
		}
		deffered.then(dojo.hitch(this, function() {
			this.onClose();
		}));
	},

	getAlteredValues: function() {
		// summary:
		//		Return a list of object properties that have been altered.
		
		// get all form values and see which values are new
		var vals = this._form.gatherFormValues();
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
			umc.tools.forIn(vals, dojo.hitch(this, function(iname, ival) {
				var oldVal = this._receivedObjFormData[iname];
				if (dojo.isArray(ival)) {
					if (dojo.toJson(ival) != dojo.toJson(oldVal)) {
						newVals[iname] = ival;
					}
				}
				// string .. ignore if empty and if it was not given before
				else {
					if (oldVal != ival) {
						newVals[iname] = ival;
					}
				}
			}));

			// set the LDAP DN
			newVals[this.moduleStore.idProperty] = vals[this.moduleStore.idProperty];
		}
		return newVals;
	},

	onClose: function() {
		// summary:
		//		Event is called when the page should be closed.
		return true;
	}
});



