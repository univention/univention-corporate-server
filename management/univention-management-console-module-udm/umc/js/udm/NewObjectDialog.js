/*
 * Copyright 2011-2012 Univention GmbH
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
	"dojo/promise/all",
	"dijit/Dialog",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, all, Dialog, tools, Text, Form, ContainerWidget, _) {

	return declare("umc.modules.udm.NewObjectDialog", [ Dialog ], {
		// summary:
		//		Dialog class for creating a new UDM object.

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

		// UDM object type name in singular and plural
		objectNameSingular: '',
		objectNamePlural: '',

		// internal reference to the dialog's form
		_form: null,

		// force max-width
		//style: 'max-width: 300px;',

		postMixInProperties: function() {
			this.inherited(arguments);

			// mixin the dialog title
			lang.mixin(this, {
				//style: 'max-width: 450px'
				title: _( 'New %s', this.objectNameSingular )
			});
		},

		buildRendering: function() {
			this.inherited(arguments);

			if ('navigation' != this.moduleFlavor) {
				// query the necessary elements to display the add-dialog correctly
				all({
					types: this.umcpCommand('udm/types', {
						superordinate: this.selectedSuperordinate !== undefined ? this.selectedSuperordinate : null
					} ),
					containers: this.umcpCommand('udm/containers'),
					superordinates: this.umcpCommand('udm/superordinates'),
					templates: this.umcpCommand('udm/templates')
				}).then(lang.hitch(this, function(results) {
					var types = lang.getObject('types.result', false, results) || [];
					var containers = lang.getObject('containers.result', false, results) || [];
					var superordinates = lang.getObject('superordinates.result', false, results) || [];
					var templates = lang.getObject('templates.result', false, results) || [];
					this._renderForm(types, containers, superordinates, templates);
				}));
			}
			else {
				// for the UDM navigation, only query object types
				this.umcpCommand('udm/types', {
					container: this.selectedContainer.id
				}).then(lang.hitch(this, function(data) {
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
			array.forEach([types, containers, templates], function(iarray) {
				iarray.sort(tools.cmpObjects('label'));
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
					label: _('Container'),
					description: _('The container in which the UDM object shall be created.'),
					staticValues: containers
				});
				layout.push('container');

				if (superordinates.length) {
					// we have superordinates
					widgets.push({
						type: 'ComboBox',
						name: 'superordinate',
						label: _('Superordinate'),
						description: _('The corresponding superordinate for the UDM object.', this.objectNameSingular),
						staticValues: superordinates,
						value: this.selectedSuperordinate
					}, {
						type: 'ComboBox',
						name: 'objectType',
						label: _('%s type', tools.capitalize(this.objectNameSingular)),
						value: this.defaultObjectType,
						description: _('The exact %s type.', this.objectNameSingular),
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
							label: _('%s type', tools.capitalize(this.objectNameSingular)),
							description: _('The exact %s type.', this.objectNameSingular),
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
					label: _('%s type', tools.capitalize(this.objectNameSingular)),
					description: _('The exact object type of the new UDM object.'),
					staticValues: types
				}, {
					type: 'ComboBox',
					name: 'objectTemplate',
					label: _('%s template', tools.capitalize(this.objectNameSingular)),
					description: _('A template defines rules for default object properties.'),
					depends: 'objectType',
					umcpCommand: this.umcpCommand,
					dynamicValues: 'udm/templates',
					staticValues: [ { id: 'None', label: _('None') } ]
				}];
				layout = [ 'container', 'objectType', 'objectTemplate' ];
			}

			// buttons
			var buttons = [{
				name: 'add',
				label: _('Add'),
				defaultButton: true,
				callback: lang.hitch(this, function() {
					this.onDone(this._form.gatherFormValues());
					this.destroyRecursive();
				}),
				style: 'float:right;'
			}, {
				name: 'close',
				label: _('Close'),
				callback: lang.hitch(this, function() {
					this.destroyRecursive();
				})
			}];

			// now create a Form
			this._form = new Form({
				widgets: widgets,
				layout: layout,
				buttons: buttons
			});
			this._form.on('submit', lang.hitch(this, function() {
				this.onDone(this._form.gatherFormValues());
				this.destroyRecursive();
			}));
			this.on('show', lang.hitch(this, function() {
				this._form.getWidget(widgets[0].name).focus();
			}));
			var container = new ContainerWidget({});
			if ('navigation' == this.moduleFlavor) {
				container.addChild(new Text({
					content: _('<p>The UDM object will be created in the the container:</p><p><i>%s</i></p>', this.selectedContainer.path)
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
});

