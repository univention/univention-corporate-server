/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._udm.NewObjectDialog");

dojo.require("dojo.DeferredList");
dojo.require("umc.i18n");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Form");
dojo.require("umc.tools");
dojo.require("umc.widgets.Text");

dojo.declare("umc.modules._udm.NewObjectDialog", [ dijit.Dialog, umc.i18n.Mixin ], {
	// summary:
	//		Dialog class for creating a new UDM object.

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.udm',

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

	// defaultObjectType: String
	//		The object type that is selected by default.
	defaultObjectType: null,

	// UDM object type name in singular and plural
	objectNameSingular: '',
	objectNamePlural: '',

	// internal reference to the dialog's form
	_form: null,

	// force max-width
	style: 'max-width: 300px;',

	postMixInProperties: function() {
		this.inherited(arguments);

		// mixin the dialog title
		dojo.mixin(this, {
			//style: 'max-width: 450px'
			title: this._( 'New %s', this.objectNameSingular )
		});
	},

	buildRendering: function() {
		this.inherited(arguments);

		if ('navigation' != this.moduleFlavor) {
			// query the necessary elements to display the add-dialog correctly
			(new dojo.DeferredList([
				this.umcpCommand('udm/types'),
				this.umcpCommand('udm/containers'),
				this.umcpCommand('udm/superordinates'),
				this.umcpCommand('udm/templates')
			])).then(dojo.hitch(this, function(results) {
				var types = results[0][0] ? results[0][1] : [];
				var containers = results[1][0] ? results[1][1] : [];
				var superordinates = results[2][0] ? results[2][1] : [];
				var templates = results[3][0] ? results[3][1] : [];
				this._renderForm(types.result, containers.result, superordinates.result, templates.result);
			}));
		}
		else {
			// for the UDM navigation, only query object types
			this.umcpCommand('udm/types', {
				container: this.selectedContainer.id
			}).then(dojo.hitch(this, function(data) {
				this._renderForm(data.result);
			}));
		}
	},

	_renderForm: function(types, containers, superordinates, templates) {
		// default values and sort items
		types = types || [];
		containers = containers || [];
		superordinates = superordinates || [];
		templates = templates || [];
		dojo.forEach([types, containers, superordinates, templates], function(iarray) {
			iarray.sort(umc.tools.cmpObjects('label'));
		});


		// depending on the list we get, create a form for adding
		// a new UDM object
		var widgets = [];
		var layout = [];

		if ('navigation' != this.moduleFlavor) {
			// we need the container in any case
			widgets.push({
				type: 'ComboBox',
				name: 'container',
				label: this._('Container'),
				description: this._('The container in which the UDM object shall be created.'),
				staticValues: containers
			});
			layout.push('container');

			if (superordinates.length) {
				// we have superordinates
				widgets.push({
					type: 'ComboBox',
					name: 'superordinate',
					label: this._('Superordinate'),
					description: this._('The corresponding superordinate for the UDM object.', this.objectNameSingular),
					staticValues: superordinates
				}, {
					type: 'ComboBox',
					name: 'objectType',
					label: this._('%s type', umc.tools.capitalize(this.objectNameSingular)),
					value: this.defaultObjectType,
					description: this._('The exact %s type.', this.objectNameSingular),
					umcpCommand: this.umcpCommand,
					dynamicValues: 'udm/types',
					depends: 'superordinate'
				});
				layout.push('superordinate', 'objectType');
			}
			else {
				// no superordinates
				// object types
				if (types.length) {
					widgets.push({
						type: 'ComboBox',
						name: 'objectType',
						value: this.defaultObjectType,
						label: this._('%s type', umc.tools.capitalize(this.objectNameSingular)),
						description: this._('The exact %s type.', this.objectNameSingular),
						staticValues: types
					});
					layout.push('objectType');
				}

				// templates
				if (templates.length) {
					templates.unshift({ id: 'None', label: this._('None') });
					widgets.push({
						type: 'ComboBox',
						name: 'objectTemplate',
						label: this._('%s template', umc.tools.capitalize(this.objectNameSingular)),
						description: this._('A template defines rules for default object properties.'),
						staticValues: templates
					});
					layout.push('objectTemplate');
				}
			}
		}
		else {
			// for the navigation, we show all elements and let them query their content automatically
			widgets = [{
				type: 'HiddenInput',
				name: 'container',
				value: this.selectedContainer.id
			}, {
				type: 'ComboBox',
				name: 'objectType',
				label: this._('%s type', umc.tools.capitalize(this.objectNameSingular)),
				description: this._('The exact object type of the new UDM object.'),
				staticValues: types
			}, {
				type: 'ComboBox',
				name: 'objectTemplate',
				label: this._('%s template', umc.tools.capitalize(this.objectNameSingular)),
				description: this._('A template defines rules for default object properties.'),
				depends: 'objectType',
				umcpCommand: this.umcpCommand,
				dynamicValues: 'udm/templates',
				staticValues: [ { id: 'None', label: this._('None') } ]
			}];
			layout = [ 'container', 'objectType', 'objectTemplate' ];
		}

		// buttons
		var buttons = [{
			name: 'add',
			label: this._('Add'),
			'default': true,
			callback: dojo.hitch(this, function() {
				this.onDone(this._form.gatherFormValues());
				this.destroyRecursive();
			})
		}, {
			name: 'close',
			label: this._('Close'),
			callback: dojo.hitch(this, function() {
				this.destroyRecursive();
			})
		}];

		// now create a Form
		this._form = new umc.widgets.Form({
			widgets: widgets,
			layout: layout,
			buttons: buttons
		});
		var container = new umc.widgets.ContainerWidget({});
		if ('navigation' == this.moduleFlavor) {
			container.addChild(new umc.widgets.Text({
				content: this._('<p>The UDM object will be created in the the container:</p><p><i>%s</i></p>', this.selectedContainer.path)
			}));
		}
		container.addChild(this._form);
		this.set('content', container);
		this.show();
	},

	onDone: function(options) {
		// event stub
	}
});



